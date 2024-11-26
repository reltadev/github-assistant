from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, Collapsible, Pretty
from textual.containers import Horizontal, VerticalScroll
from textual.binding import Binding
from ..client import Client
from ..datasource import DataSource
from rich.text import Text
from rich.syntax import Syntax
from ..agents.semantic_agent import (
    SemanticAgent,
    State as SemanticState,
)
import difflib
from rich.spinner import Spinner
from textual import log as textual_log
import sqlparse

INSTRUCTIONS = """
[italic green]Welcome to the semantic layer builder.[/italic green]
[sea_green3][bold]Usage:[/bold] provide the agent instructions to refine the semantic layer, e.g.:

- "create metrics to support questions like: ..."
- "build a way to track critical routes, which are routes that have been flown more than 1000 times"

Changes build over multiple messages. 
You can choose to approve or reject changes to the semantic layer with `a` and `r`.
You can quit with `q`. [/sea_green3]
"""


class WizardApp(App):
    """A Textual app for Relta chat interface."""

    BINDINGS = [
        Binding("d", "toggle_dark", "Toggle dark mode", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("a", "layer_approve", "Approve changes", show=True),
        Binding("r", "layer_reject", "Reject changes", show=True),
        Binding("c", "user_chat_clear", "Clear user chat", show=True),
    ]

    def __init__(self, client: Client, source: DataSource):
        self.client = client
        self.source = source
        if source.semantic_layer.metrics:
            source.deploy(statistics=False)

        self.chat = client.create_chat(source)
        self.agent = SemanticAgent()
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Horizontal(
            VerticalScroll(
                Collapsible(
                    RichLog(id="chat_log", wrap=True),
                    Input(placeholder="Enter your prompt here...", id="prompt_input"),
                    id="chat_container",
                    title="Layer Builder Chat",
                    collapsed=False,
                ),
                Collapsible(
                    RichLog(id="true_chat_log", wrap=True),
                    Input(
                        placeholder="Enter your prompt here...", id="true_prompt_input"
                    ),
                    id="true_chat_container",
                    title="Enduser Chat",
                ),
            ),
            VerticalScroll(
                Collapsible(
                    RichLog(id="metrics_log", wrap=True),
                    id="layer_container",
                    title="Semantic Layer",
                    collapsed=False,
                ),
                Collapsible(
                    RichLog(id="ddl_log"),
                    id="ddl_container",
                    title="DataSource DDL",
                ),
                Collapsible(
                    Pretty([], id="sql_results"),
                    id="results_container",
                    title="SQL Results",
                ),
            ),
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Relta Semantic Layer Wizard"
        self.sub_title = f"Datasource: {self.source.name}"

        chat_log = self.query_one("#chat_log", RichLog)
        chat_log.write(Text.from_markup(INSTRUCTIONS))
        true_chat_log = self.query_one("#true_chat_log", RichLog)
        true_chat_log.write(Text.from_markup("[italic]Sample User Chat[/italic]"))

        ddl_log = self.query_one("#ddl_log", RichLog)

        statements = sqlparse.split(self.source._get_ddl())
        statements = [
            sqlparse.format(statement, reindent=True) for statement in statements
        ]
        for statement in statements:
            ddl_log.write(Syntax(statement, "sql", word_wrap=True))

        self.proposed_layer_str = ""
        self._update_metrics_window()

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Handle submitted prompt."""
        if message.input.id == "prompt_input":
            input_widget = self.query_one("#prompt_input", Input)
            chat_log = self.query_one("#chat_log", RichLog)
        else:
            input_widget = self.query_one("#true_prompt_input", Input)
            chat_log = self.query_one("#true_chat_log", RichLog)
        # elif message.input.id == "true_prompt_input":

        # input_widget = self.query_one("#prompt_input", Input)
        # chat_log = self.query_one("#chat_log", RichLog)
        # metrics_log = self.query_one("#metrics_log", RichLog)

        # Add user message to log
        chat_log.write(Text.from_markup(f"[bold blue]You:[/bold blue] {message.value}"))

        # spinner animation requires something to update it, which we're not doing right now
        chat_log.write(Spinner("dots", "Processing..."))

        # Clear input after sending
        input_widget.value = ""

        if message.input.id == "prompt_input":
            try:
                # TODO: add asyncio create task here
                state: SemanticState = await self.agent.ainvoke(
                    message=message.value,
                    layer=self.source.semantic_layer,
                    thread_id=0,  # we are using an in-memory saver so this will always be clear the next time the wizard is launched.
                )
                textual_log.info(state)
                self.source.semantic_layer._update(state["curr_update"].semantic_layer)
                # TODO: verify this is a good idea... it prob is, but should we clean it up?
                self.source.deploy(statistics=False)
            except Exception as e:
                chat_log.lines.pop()
                chat_log.write(Text.from_markup(f"[bold red]Exception:[/bold red] {e}"))
                return

            chat_log.lines.pop()

            chat_log.write(
                Text.from_markup(
                    f"[bold green]Relta:[/bold green] {state['messages'][-1].content}"
                )
            )
        else:
            try:
                resp = self.chat.prompt(message.value)
            except Exception as e:
                chat_log.lines.pop()
                chat_log.write(Text.from_markup(f"[bold red]Exception:[/bold red] {e}"))
                return

            chat_log.lines.pop()
            chat_log.write(
                Text.from_markup(f"[bold green]Relta:[/bold green] {resp.text}")
            )
            chat_log.write(
                Text.from_markup(f"[bold purple]SQL:[/bold purple] {resp.sql}")
            )
            results = self.query_one("#sql_results", Pretty)
            results.update(resp.sql_result)

        # make a diff
        # d = self.source.semantic_layer.metrics[0].dimensions
        # d.append(
        #     Dimension(
        #         name="test", description="testing dim", categories=None, dtype="string"
        #     )
        # )
        # d[0].name = "test2"
        ###

        # chat_log.lines.pop()

        # chat_log.write(
        #     Text.from_markup(
        #         f"[bold green]Relta:[/bold green] {state['messages'][-1].content}"
        #     )
        # )

        self.proposed_layer_str = self.source.semantic_layer.dumps()
        self._update_metrics_window()

    def action_user_chat_clear(self) -> None:
        """Clear the user chat."""
        chat_log = self.query_one("#true_chat_log", RichLog)
        chat_log.clear()
        self.chat = self.client.create_chat(self.source)

    def action_layer_approve(self) -> None:
        """Approve changes to the semantic layer. This is equivalent to dumping the changes."""
        self.source.semantic_layer.dump()
        self.proposed_layer_str = ""
        self._update_metrics_window()

    def action_layer_reject(self) -> None:
        """Reject changes to the semantic layer. This is equivalent to loading in the previous layer, which is always saved on disk before."""
        self.source.semantic_layer.load()
        self.proposed_layer_str = ""
        self._update_metrics_window()

    def _update_metrics_window(self) -> None:
        """Update the metrics window, using the proposed layer string if it exists."""
        metrics_log = self.query_one("#metrics_log", RichLog)
        if self.proposed_layer_str:
            diff = list(
                difflib.ndiff(
                    self.curr_layer_str.splitlines(keepends=True),
                    self.proposed_layer_str.splitlines(keepends=True),
                )
            )
            s = "".join(diff)
        else:
            s = self.source.semantic_layer.dumps()
            self.curr_layer_str = s
        metrics_log.clear()
        metrics_log.write(Syntax(s, "json", word_wrap=True))

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


if __name__ == "__main__":
    rc = Client()
    app = WizardApp(rc, rc.get_datasource("db"))
    app.run()
