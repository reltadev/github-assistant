from typing import Annotated, Optional, ClassVar, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, AnyMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from ..datasource import DataSource
from typing_extensions import TypedDict
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from ..config import Configuration
from ..semantic.base import Example, Metric
from langchain_core.runnables.config import RunnableConfig

METRIC_MATCH_PROMPT = """
You are a SQL & data modeling expert with strong attention to detail. 

### Definitions:
- A metric is a named set of dimensions and measures that can be used to answer a question. It is a SQL view.
- Dimensions are like columns in a view -- they can be used to group or filter data.
- Measures are aggregate operations on dimensions -- they can be used to calculate sums, averages, counts, etc.

### Task:
Given an input question, previous chat history, and a list of metrics in JSON, choose a single metric that can answer the user's question. Write your response in the JSON schema provided with reasoning.

Let's think step by step. 
First, read the metric definitions to understand what you can answer for. 
Next, read the user's question and the chat history to understand the user's intent. 
If the user's question is not clear or if the metric indicates that it needs additional information, 

### Guidelines:
- If the user's question is not clear or does not require SQL to be generated, respond with "None" but provide reasoning. 
- If there is no relevant metric, respond with "None" but provide reasoning.
- The user's current question is at the bottom of the chat history, contained in the rest of the messages.

--
# Metrics:
{metrics}
"""

MATCH_PROMPT = """You are a SQL expert with strong attention to detail. 

### Definitions:
- A metric is a named set of dimensions and measures that can be used to answer a question. It is a SQL view.
- Dimensions are like columns in a view -- they can be used to group or filter data.
- Measures are aggregate operations on dimensions -- they can be used to calculate sums, averages, counts, etc.

### Task:
Given an input question, previous chat history, and a chosen metric in JSON, generate a syntactically correct PostgreSQL query to run, potentially using dimensions as WHERE or GROUP BY expressions and measures as HAVING expressions.
Please return this in the JSON schema provided.

### Rules:
- The SQL query can only use the chosen metric's dimensions and measures.
- You should err on the side of returning more data than less -- for example, if there are multiple columns referencing "usage" and a query about "usage", you can return multiple of them.
- To use a measure, you must use exactly the "agg_operation" and "expr" fields in the measure. The name of the measure is the alias to use in the SELECT clause.
Example:
{{
    "measures": [
        {{
            "name": "total_sales",
            "expr": "SUM(price * quantity)"
        }}
    ]
}}
Then, to use the total_sales measure in the query, you would write
SELECT SUM(price * quantity) as total_sales FROM ...;

- You should add a LIMIT 100 to the SQL query to limit the amount of data returned.
- The SQL query should not include any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
- The output string should not start with "```sql" or end with "```" -- it should just be the query.
- You may use a subquery in the FROM clause and nest subqueries, but you can only use that same metric for the entire query.
- You should not chain 
- The metric is a view, so to use it, it should be referenced by its name in a FROM clause.
- Ignore the "sql_to_underlying_datasource" field in the metric.
"""

# TODO: tell it to assume little about data arrangmennt, so "how many listening minutes for disney" should use a LOWER(vendor) like (%disney%) instead of = "disney".
# TODO: if needing to repair a query, consider using "sql_to_underlying_datasource"

RESPONSE_PROMPT = """
Using the data from the executed SQL query, write a response to the user's question. If the SQL generated uses a categorical dimension to filter by, mention the value(s) used.
If there is not data from an executed SQL query, check these cases:
- The question appears related to a metric but was not answerable. If so, ask the user to clarify and include what you can provide in the metrics.
- The question was not related to any metrics. Redirect the user to ask a question about the metrics available.
- If the SQL query failed, ask the user to clarify and reformulate the question.

The user question is:
{user_question}

The relevant SQL generation that the agent produced previously is:
{sql_generation}

The data from the executed SQL query is:
{query_results}

See attached chat history for context.
"""

# TODO: query failure handling

REPAIR_PROMPT = """
You are a SQL expert.
The following PostgreSQL query failed with this error: {ERROR}

Original SQL:
{SQL}

It is running this against a database with this DDL:
{TRANSIENT_DDL}

The context of the conversation is attached, with the last question being the user's question.

Please analyze the error and provide a corrected version of the SQL query.
Please return this in the JSON schema provided.

## Guidelines:
- The output string should not start with "```sql" or end with "```" -- it should just be the query.
- Set the "metric" field to the name of the table in FROM.
- You cannot do any JOINs in the query.
- If you cannot correct the query, populate the "sql" field with 'None'.
"""

FUZZ_PROMPT = """
Given the following SQL query, generate fake data response that could have been returned by executing this query.
For example,
SELECT SUM(price * quantity) as total_sales, sku FROM sales GROUP BY sku;

Could return:
[
    {{"total_sales": 100, "sku": "Bike"}},
    {{"total_sales": 200, "sku": "Air Pump"}},
]

Please return this in the JSON schema provided.
"""


class FuzzedData(BaseModel):
    data: list[dict[str, Any]] = Field(
        description="List of rows of fake data that could be returned by the query. Each element of the list is a dict with the 'SELECT' objects as keys that map to one int/str/etc. for that row. You must return something here, it can be limited to a 1-10 rows."
    )
    reasoning: str = Field(
        description="A <20 word explanation of how the fake data was generated."
    )

    class Config:
        arbitrary_types_allowed = True


class SQLGeneration(BaseModel):
    metric: Optional[str] = Field(
        description="The name of the metric that was chosen. If there was no metric chosen, respond with 'None'."
    )
    metric_reasoning: Optional[str] = Field(
        description="The reasoning that led to the chosen metric or to not choosing a metric. Keep it within 2 sentences."
    )
    sql: Optional[str] = Field(
        description="""
        The SQL query that was generated. 
        This should be "None" if you are currently selecting a metric.
        If there was no metric chosen, respond with 'None'. 
        If a metric was chosen, but you couldn't generate a SQL query, respond with 'None'.
        """
    )
    sql_reasoning: Optional[str] = Field(
        description="The reasoning that led to the SQL query or to not generating a SQL query. Keep it within 2 sentences. This should be 'None' if you are currently selecting a metric."
    )


class AgentConfig(TypedDict):
    thread_id: Optional[int]
    only_sql: bool
    fuzz: bool


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    metrics: list[Metric]  # potentially config, fetched through datasource?
    examples: list[Example]
    datasource: DataSource  # potentially config
    sql_generation: SQLGeneration
    query_results: list
    sql_execution_error: str
    n_retries: int


class SQLAgent:
    """Default SQL Generation Agent.

    Supports persisting threads. Directly generates SQL from DDL. Used internally for `relta.chat.Chat`
    """

    model: ClassVar[ChatOpenAI]  # populated by Client
    mini_model: ClassVar[ChatOpenAI]  # populated by Client
    _config: Configuration

    @staticmethod
    def mask_metrics(metrics: list[Metric]) -> list[Metric]:
        """Note: this is not a node!"""
        masked_metrics = [m.model_copy(deep=True) for m in metrics]
        for metric in masked_metrics:
            metric.sql_to_underlying_datasource = None
        return masked_metrics

    @staticmethod
    def select_metric(state: State, config: RunnableConfig):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", METRIC_MATCH_PROMPT),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt_template | SQLAgent.model.with_structured_output(SQLGeneration)
        masked_metrics = SQLAgent.mask_metrics(state["metrics"])

        # TODO avoid generating SQL, but for now, wipe out the SQL fields
        res: SQLGeneration = chain.invoke(
            {
                "metrics": [m.model_dump_json() for m in masked_metrics],
                "messages": state["messages"],
            }
        )
        res.sql = None
        res.sql_reasoning = None

        return {"sql_generation": res}

    @staticmethod
    def generate_sql(state: State, config: RunnableConfig):
        # examples_str = "Examples:\n{examples}\n"
        # examples_str = ""
        # for example in state["examples"]:
        # examples_str += f"### Example\n#### Prompt\n{example.prompt}\n\n#### SQL\n{example.sql}\n\n#### Explanation\n{example.explanation}\n\n"
        sql_gen = state["sql_generation"]
        if sql_gen.metric is None or sql_gen.metric.lower() == "none":
            return {"messages": [SystemMessage("No metric chosen.")]}

        # TODO filter examples by metric?
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", MATCH_PROMPT),
                ("system", "Metric:\n{metric}"),
                ("system", "Examples:\n{examples}\n"),
                # ("system", f"Read the prompt again: \n{MATCH_PROMPT}"),
                ("placeholder", "{messages}"),
            ]
        )
        chain = prompt_template | SQLAgent.model.with_structured_output(SQLGeneration)
        masked_metrics = SQLAgent.mask_metrics(state["metrics"])
        matched_metric = [
            m.model_dump_json() for m in masked_metrics if m.name == sql_gen.metric
        ][0]

        res: SQLGeneration = chain.invoke(
            {
                "metric": matched_metric,
                "examples": [e.model_dump_json() for e in state["examples"]],
                "messages": state["messages"],
            }
        )

        return {"sql_generation": res}

    @staticmethod
    def execute_sql(state: State, config: RunnableConfig):
        # sql_gen = SQLGeneration.model_validate_json(state["sql_generation"])
        sql_gen = state["sql_generation"]
        sql = sql_gen.sql

        if (
            sql is None
            or sql.lower() == "none"
            or sql_gen.metric.lower() == "none"
            or sql_gen.metric is None
        ):
            return {
                "messages": [SystemMessage("No SQL query generated.")],
            }

        if config["configurable"]["fuzz"]:
            # random fuzzing (fast) w/ sqlglot, numpy
            # outp = {}
            # for select in parse_one(sql).find_all(exp.Select):
            #     for projection in select.expressions:
            #         outp[projection.alias_or_name] = np.random.randint(0, 100)
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
            prompt_template = ChatPromptTemplate.from_messages(
                [
                    ("system", FUZZ_PROMPT),
                    ("system", "{sql}"),
                    ("system", "Here is an interpretation of the DDL for the table:"),
                    ("system", "{metrics}"),
                    # ("placeholder", "{messages}"),
                ]
            )
            chain = prompt_template | llm.with_structured_output(FuzzedData)

            masked_metrics = SQLAgent.mask_metrics(state["metrics"])

            res: FuzzedData = chain.invoke(
                {
                    "sql": sql,
                    "metrics": [m.model_dump_json() for m in masked_metrics],
                    # "messages": state["messages"],
                }
            )
            outp = res.data
        else:
            try:
                outp = state["datasource"]._execute_sql(sql).fetchall()
            except Exception as e:
                return {
                    "messages": [SystemMessage(f"Error executing SQL: {str(e)}")],
                    "sql_execution_error": str(e),
                    "query_results": [],
                }

        return {
            "query_results": outp,
            "sql_execution_error": None,
            # "messages": [AIMessage(state["sql_generation"].model_dump_json())],
        }

    @staticmethod
    def repair_sql(state: State, config: RunnableConfig):
        # improve this
        # only runs if there is a failure code.
        sql_gen = state["sql_generation"]
        # sql_gen = SQLGeneration.model_validate_json(state["sql_generation"])
        # user_prompt = state["messages"][-3].content

        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", REPAIR_PROMPT),
                ("placeholder", "{messages}"),
            ]
        )

        chain = prompt_template | SQLAgent.model.with_structured_output(SQLGeneration)
        res: SQLGeneration = chain.invoke(
            {
                "SQL": sql_gen.sql,
                "ERROR": state["sql_execution_error"],
                "TRANSIENT_DDL": state["datasource"]._get_transient_ddl(),
                "messages": state["messages"],
            }
        )

        return {"sql_generation": res, "n_retries": state["n_retries"] - 1}

    @staticmethod
    def respond(state: State, config: RunnableConfig):
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", RESPONSE_PROMPT),
                ("system", MATCH_PROMPT),
                ("system", "{metrics}"),
                ("placeholder", "{messages}"),
                ("system", "{query_results}"),
            ]
        )

        # Find the last HumanMessage in state messages
        user_question = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                user_question = msg.content
                break

        chain = prompt_template | SQLAgent.model
        res = chain.invoke({**state, "user_question": user_question})
        return {"messages": [AIMessage(state["sql_generation"].model_dump_json()), res]}

    def __init__(self, config: Configuration):
        self._config = config
        self.checkpointer = SqliteSaver(
            sqlite3.connect(self._config.chat_memory_path, check_same_thread=False)
        )

        graph_builder = StateGraph(State)

        graph_builder.add_node("select_metric", SQLAgent.select_metric)
        graph_builder.add_node("generate_sql", SQLAgent.generate_sql)
        graph_builder.add_node("execute_sql", SQLAgent.execute_sql)
        graph_builder.add_node("repair_sql", SQLAgent.repair_sql)
        graph_builder.add_node("response", SQLAgent.respond)

        graph_builder.add_edge(START, "select_metric")
        graph_builder.add_edge("select_metric", "generate_sql")
        # graph_builder.add_conditional_edges(
        #     "select_metric",
        #     lambda state, config: "generate_sql"
        #     if state.get("sql_generation", None) and state["sql_generation"].metric is not None
        #     else END,
        # )
        graph_builder.add_conditional_edges(
            "generate_sql",
            lambda state, config: "execute_sql"
            if not config["configurable"]["only_sql"]
            else END,
        )
        graph_builder.add_conditional_edges(
            "execute_sql",
            lambda state, config: "repair_sql"
            if state.get("sql_execution_error", None) is not None
            and state.get("n_retries", 0) > 0
            else "response",
        )
        graph_builder.add_edge("repair_sql", "execute_sql")
        graph_builder.add_edge("response", END)

        self.graph = graph_builder.compile(checkpointer=self.checkpointer)

    def _get_mermaid(self):
        return self.graph.get_graph().draw_mermaid()

    def invoke(
        self,
        prompt: str,
        datasource: DataSource,
        thread_id: Optional[int] = None,
        debug: Optional[bool] = None,
        only_sql: bool = False,
        fuzz: bool = False,
        n_retries: int = 1,
    ) -> State:
        """Ask the agent a question.

        Args:
            prompt (str): Question
            datasource (DataSource): datasource to use for the question
            thread_id (int, optional): ID of the thread/chat to use for persistence. If None, runs the graph on a non-persisted thread. Defaults to None.
            debug (bool, optional): If True, runs the graph in debug mode. If None, uses the default value set in the config. Defaults to None.
            only_sql (bool, optional): If True, skips the response node and only returns the generated SQL. Defaults to False.
            fuzz (bool): Use an LLM to generate fake query results instead of executing the SQL. Defaults to False.
            n_retries (int, optional): Number of times to attempt to repair the SQL if the SQL execution fails. Defaults to 1.
        Returns:
            State: full state of the agent after the invocation
        """
        if debug is None:
            debug = self._config.debug

        state_update: State = {
            "messages": [HumanMessage(prompt)],
            "metrics": datasource.semantic_layer.metrics,
            "examples": datasource.semantic_layer.examples,
            "datasource": datasource,
            "sql_generation": None,
            "sql_execution_error": None,
            "n_retries": n_retries,
            "query_results": None,
        }

        config: AgentConfig = {
            "only_sql": only_sql,
            "fuzz": fuzz,
            "thread_id": thread_id,
        }

        return self.graph.invoke(
            state_update,
            config={"configurable": config},
            debug=debug,
        )
