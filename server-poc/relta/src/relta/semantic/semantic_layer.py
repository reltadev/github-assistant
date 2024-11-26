from .base import (
    Example,
    ExampleCollection,
    Metric,
    ProposedMetrics,
    RefinedMetrics,
    Feedback,
    SemanticLayerContainer,
)
from .prompts import SYSTEM_PROMPT_SEMANTIC_LAYER_BUILDER, REFINE_SEMANTIC_LAYER_PROMPT
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
from os import makedirs
from typing import Optional, Union
from pathlib import Path
from ..config import Configuration
import logfire
from github import Github
from github.GithubException import GithubException
import uuid
import logging

logger = logging.getLogger(__name__)


class SemanticLayer:
    def __init__(
        self,
        datasource: "DataSource",  # noqa: F821 # type: ignore
        config: Configuration,
        load: bool = True,
        path: Optional[str] = None,
    ):
        from ..datasource import (
            DataSource,
        )  # this is to allow type hinting when writing code w/o a circular import (similar to other libraries)

        self._config = config
        self.datasource: DataSource = datasource
        self.path = (
            self._config.relta_semantic_layer_dir_path / self.datasource.name
            if path is None
            else Path(path)
        )
        self.update_reasoning: str = (
            ""  # semantic agent will write reasoning about the update here
        )
        self.feedback_responses = []
        self.metrics: list[Metric] = []
        self.examples: list[Example] = []
        # self.proposed_changes: list[Metric] = []
        makedirs(self.path, exist_ok=True)
        if load:
            self.load()

    def load(self, path: Optional[Union[str, Path]] = None):
        """Load semantic layer.

        Changes to the metrics are not persisted on disk. Use `.dump()` to persist them.

        Args:
            path (Optional[Union[str, Path]], optional): Path to load the semantic layer. If None, uses `self.path`, which is populated on creation.
        """
        logfire.info("loading semantic layer from {path}", path=str(path))
        metrics = []
        examples = []
        p = Path(path) if path is not None else self.path

        for fpath in p.glob("*.json"):
            with open(fpath, "r") as f:
                if fpath.name == "examples.json":
                    example_coll = ExampleCollection.model_validate_json(f.read())
                    examples.extend(example_coll.examples)
                else:
                    metrics.append(Metric.model_validate_json(f.read()))
        self.metrics = metrics
        self.examples = examples

    def dump(
        self,
        clear=True,
        path: Optional[Union[str, Path]] = None,
        # apply_proposals: bool = True,
    ):
        """Dumps the semantic layer, accepting any updates made to the semantic layer.

        Args:
            clear (bool): Delete all JSON files in the path for this layer. Defaults to True. See `path` attribute for details on the path.
            path (Optional[Union[str, Path]], optional): Path to dump the semantic layer. If None, uses `self.path`, which is populated on creation.
        """

        logfire.info("dumping semantic layer to file")
        p = path if path is not None else self.path

        if clear:
            for json_file in p.glob("*.json"):
                json_file.unlink()

        for metric in self.metrics:
            with open(p / f"{metric.name}.json", "w+") as f:
                f.write(metric.model_dump_json(indent=2))

        examples = ExampleCollection(examples=self.examples)
        with open(p / "examples.json", "w+") as f:
            f.write(examples.model_dump_json(indent=2))

        # additionally, as dumping is "accepting" the changes, we clean up any updated state
        self.update_reasoning = ""

    def dumps(self, **kwargs) -> str:
        """Dumps the metrics and examples to a JSON string. Used for diffing.

        Args:
            **kwargs: Keyword arguments to pass to `pydantic.BaseModel.model_dump_json`. Will override, by individual key, Relta's default kwargs for printing.

        Returns:
            str: JSON representation of the semantic layer (metrics and examples).
        """
        default_kwargs = {"indent": 2}
        default_kwargs.update(kwargs)

        return SemanticLayerContainer(**vars(self)).model_dump_json(**default_kwargs)

    def refine(self, pr=False):
        """Refines the semantic layer based on the feedback and creates a PR with the changes."""
        logfire.info("refine semantic layer")
        llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(
            RefinedMetrics
        )
        prompt = PromptTemplate.from_template(REFINE_SEMANTIC_LAYER_PROMPT)

        chain = prompt | llm

        feedback = [
            Feedback(
                sentiment=r.feedback_sentiment,
                reason=r.feedback_reason,
                selected_response=r.message,
                message_history=r.chat._get_messages(),
            )
            for r in self.feedback_responses
        ]

        result: RefinedMetrics = chain.invoke(
            {
                "METRIC_MODEL": json.dumps(
                    Metric.model_json_schema(mode="serialization"), indent=2
                ),
                "METRICS": json.dumps(
                    [metric.model_dump() for metric in self.metrics], indent=2
                ),
                "FEEDBACK": json.dumps(
                    [feedback.dict() for feedback in feedback], indent=2
                ),
                "DDL": self.datasource._get_ddl(),
            }
        )

        existing_metrics = {m.name: m for m in self.metrics}
        refined_metrics = {m.original_name: m.updated_metric for m in result.metrics}

        for name, refined_metric in refined_metrics.items():
            if name in existing_metrics:
                existing_metric = existing_metrics[name]
                print(f"Metric: {name}")

                for field in Metric.model_fields:
                    refined_value = getattr(refined_metric, field)
                    existing_value = getattr(existing_metric, field)
                    if refined_value != existing_value:
                        print(f"  {field}:")
                        print(f"    - Old: {existing_value}")
                        print(f"    + New: {refined_value}")

                        # Handle list fields like dimensions, measures, sample_questions
                        if isinstance(refined_value, list):
                            refined_set = set(str(x) for x in refined_value)
                            existing_set = set(str(x) for x in existing_value)

                            removed = existing_set - refined_set
                            added = refined_set - existing_set

                            if removed:
                                print("    Removed items:")
                                for item in removed:
                                    print(f"      - {item}")

                            if added:
                                print("    Added items:")
                                for item in added:
                                    print(f"      + {item}")

                print()
            else:
                print(f"New Metric: {name}")
                print(f"  + {refined_metric.model_dump_json(indent=2)}")
                print()

        # for metric_container in result.metrics:
        #     self.proposed_changes.append(metric_container.updated_metric)
        self.metrics = [m.updated_metric for m in result.metrics]

        if pr:
            # Create a new branch and open a PR with the refined metrics
            res = self._create_pr_with_refined_metrics(
                [update.updated_metric for update in result.metrics]
            )
            if not res:
                print("Failed to create a PR.")
                # self.dump()
        else:
            print("Not creating a PR.")
            # self.dump()

        return [update.updated_metric for update in result.metrics]

    def _create_pr_with_refined_metrics(self, refined_metrics: list[Metric]):
        """Creates a new branch with refined metrics and opens a PR."""
        try:
            g = Github(self._config.github_token)
            repo = g.get_repo(self._config.github_repo)

            # Create a new branch
            base_branch = repo.get_branch(self._config.github_base_branch)
            branch_name = f"refined-metrics-{uuid.uuid4().hex[:8]}"
            repo.create_git_ref(f"refs/heads/{branch_name}", base_branch.commit.sha)

            # Update metrics files in the new branch
            for metric in refined_metrics:
                file_path = f"{self._config.relta_semantic_layer_dir_path}/{self.datasource.name}/{metric.name}.json"
                content = metric.model_dump_json(indent=2)

                try:
                    file = repo.get_contents(file_path, ref=branch_name)
                    repo.update_file(
                        file_path,
                        f"Update {metric.name} metric",
                        content,
                        file.sha,
                        branch=branch_name,
                    )
                except GithubException:
                    repo.create_file(
                        file_path,
                        f"Add {metric.name} metric",
                        content,
                        branch=branch_name,
                    )

            # Create a pull request
            pr_title = f"Refined metrics for {self.datasource.name}"
            pr_body = "This PR contains refined metrics based on user feedback."
            repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=self._config.github_base_branch,
            )

            print(f"Created a pull request with refined metrics: {pr_title}")
            return True
        except Exception as e:
            print(f"Error creating PR with refined metrics: {str(e)}")
            return False

    def copy(
        self,
        source: "DataSource",  # noqa: F821
        dump: bool = True,
    ):
        """Copy the semantic layer from another DataSource.

        Args:
            source (DataSource): `DataSource` object to copy the semantic layer from.
            # from_path (Optional[Union[str, Path]], optional): Path to load the semantic layer from, ignoring `source`. If None, uses `source`'s semantic layer. Defaults to None.
            dump (bool, optional): Whether to dump the semantic layer to it's path. Defaults to True.
        """
        # if from_path is None:
        self.metrics = [
            metric.model_copy(deep=True) for metric in source.semantic_layer.metrics
        ]
        self.examples = [
            example.model_copy(deep=True) for example in source.semantic_layer.examples
        ]
        # else:
        #     self.load(from_path)

        if dump:
            self.dump()

    def propose(
        self,
        queries: list[str],
        context: Optional[str] = None,
    ):
        """Proposes a new semantic layer for the given datasource and natural language queries.

        Args:
            queries (list[str]): A list of natural language queries that the semantic layer should answer.
            context (Optional[str], optional): Extra information about the datasource. Defaults to None.
        """
        logfire.span("proposing new semantic layer")
        proposed_metrics = self._generate_proposed_metrics(
            [self.datasource._get_ddl()],
            queries,
            self.datasource.name,
            context,
        )
        for m in proposed_metrics.metrics:
            if m.name.lower() == "example":
                m.name = "example_ds"
                logger.info(
                    "Renamed metric 'example' to 'example_ds' to avoid collision with few shot examples."
                )

        self.metrics = proposed_metrics.metrics
        logfire.info(
            "{num_metrics} metrics proposed in semantic layer",
            num_metrics=len(self.metrics),
        )

    def show(self):
        """Prints table of metrics."""
        raise NotImplementedError()

    def _update(self, container: SemanticLayerContainer):
        self.metrics = container.metrics
        self.examples = container.examples
        self.update_reasoning = container.update_reasoning

    @staticmethod
    def _generate_proposed_metrics(
        ddl: list[str],
        questions: list[str],
        source_name: str,
        context: Optional[str] = None,
    ) -> ProposedMetrics:
        """Generates a list of metrics for the given datasource and natural language queries.

        Args:
            ddl (list[str]): The DDL for the datasource.
            questions (list[str]): A list of natural language queries that the semantic layer should answer.
            source_name (str): The name of the datasource.
            context (str, optional): Extra information about the datasource. Defaults to None.
        """
        llm = ChatOpenAI(
            model="gpt-4o-2024-08-06", temperature=0
        ).with_structured_output(ProposedMetrics)
        prompt = PromptTemplate.from_template(SYSTEM_PROMPT_SEMANTIC_LAYER_BUILDER)

        chain = prompt | llm  # | parser
        result: ProposedMetrics = chain.invoke(
            {
                "QUESTIONS": "\n".join(questions),
                "DDL": "\n".join(ddl),
                "CONTEXT": context,
                "DATASOURCE_NAME": source_name,
            }
        )

        return result
