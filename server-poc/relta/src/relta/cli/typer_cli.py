import typer
from rich.panel import Panel
from rich.console import Console
from rich.syntax import Syntax
from typing import Optional
import relta
import sqlparse
from functools import wraps
from pathlib import Path

app = typer.Typer(no_args_is_help=True)
console = Console()
if Path("./.relta").exists():
    rc = relta.Client()
else:
    rc = None

from .textual_cli import WizardApp  # noqa: E402 # this is because openai_api_key is not yet set. TODO: find a better solution.


def catch_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            raise typer.Exit(code=1)

    return wrapper


def relta_cmd(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if rc is None:
            console.print(
                "Relta not set up in current folder -- try [green]relta init[/green]"
            )
            raise typer.Exit(code=1)
        return catch_exceptions(func)(*args, **kwargs)

    return wrapper


@app.command()
@catch_exceptions
def init():
    """
    Initialize Relta in the current folder.
    """
    relta.Client()
    console.print("[green]Relta initialized. Please commit changes to `.relta`[/green]")


@app.command()
@relta_cmd
def create(conn_uri: str, name: Optional[str] = None):
    """
    Create a new DataSource, optionally specifying a name (--name).

    Supports Postgres DSN and CSV paths.
    If --name is not provided, Relta will infer a name from the connection URI.
    """
    source = rc.create_datasource(conn_uri, name)
    console.print(f'Added ⛁ Datasource "[green]{source.name}[/green]"')


@app.command()
@relta_cmd
def list():
    """List all DataSources"""
    sources = rc.get_sources()
    if len(sources) == 0:
        console.print("No datasources found")
    else:
        for source in sources:
            console.print(f"  - [green]{source.name}[/green]")


@app.command()
@relta_cmd
def delete(name: str):
    """Delete a DataSource"""
    rc.delete_datasource(name)
    console.print(f"Deleted ⛁ Datasource [green]{name}[/green]")


@app.command()
@relta_cmd
def layer(
    name: str,
    #   filter: Optional[str] = None
):
    """Print the semantic layer for a DataSource"""
    source = rc.get_datasource(name)
    if source is None:
        raise Exception(f"No datasource with name [bold red]{name}[/bold red] found")

    metrics_json = [m.model_dump_json(indent=2) for m in source.semantic_layer.metrics]
    metrics_json = "[\n" + ",\n".join(metrics_json) + "\n]"
    console.print(
        Panel(
            Syntax(metrics_json, "json"),
            title=f"Semantic Layer for {name}",
        )
    )


@app.command()
@relta_cmd
def propose(
    name: str,
    # context: Annotated[
    #     str,
    #     typer.Option(
    #         prompt_required=False,
    #         show_default=True,
    #         prompt="Enter in business context for the datasource",
    #     ),
    # ] = "",
):
    """
    Generate a semantic layer for a DataSource.

    Note that this will overwrite the existing semantic layer.
    """
    source = rc.get_datasource(name)

    context = console.input("Enter in business context for the datasource: ")

    questions = []
    console.print("Enter user questions to support. Type 'done' when finished.")
    while True:
        question = console.input("[bold]?:[/bold] ")
        if question.lower() == "done":
            break
        questions.append(question)

    if not questions:
        console.print("No questions provided. Exiting.")
        return

    with console.status("Proposing semantic layer...", spinner="dots"):
        source.semantic_layer.propose(questions, context)
        source.semantic_layer.dump()
    console.print(
        "[green]Semantic layer proposal complete.[/green] See '[yellow]relta layer[/yellow]' to view."
    )


@app.command()
@relta_cmd
def deploy(name: str):
    """
    Deploy the semantic layer for a DataSource, which copies the data from the source that is relevant to the semantic layer.
    """
    source = rc.get_datasource(name)
    with console.status("Deploying semantic layer...", spinner="dots"):
        source.deploy()
    console.print(
        f"Semantic layer for [green]{name}[/green] has been deployed successfully."
    )


@app.command()
@relta_cmd
def chat(name: str, sql: bool = False):
    """
    Create a chat on a DataSource for testing and demo purposes.

    If --sql is passed, the metric and SQL information will be printed in the chat.
    """
    source = rc.get_datasource(name)
    source.deploy()
    chat = rc.create_chat(source)
    console = Console()
    console.print("Exit chat with 'exit', 'quit', or 'q'")
    while True:
        user_input = console.input("[bold blue]You:[/bold blue] ")
        if user_input.lower() in ["exit", "quit", "q"]:
            break

        try:
            response = chat.prompt(user_input)
            console.print("[bold green]AI:[/bold green]", response.text)
            if response.sql and sql:
                console.print("[bold yellow]SQL:[/bold yellow]")
                formatted_sql = sqlparse.format(
                    response.sql, reindent=True, keyword_case="upper"
                )
                console.print(formatted_sql)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")


@app.command()
@relta_cmd
def wizard(name: str):
    """
    Conversational TUI for setting up a semantic layer for a DataSource.
    """
    source = rc.get_datasource(name)
    if source is None:
        raise Exception(f"No datasource with name [bold red]{name}[/bold red] found")

    wizard_app = WizardApp(
        client=rc,
        source=source,
    )
    wizard_app.run()


def run():
    app()


if __name__ == "__main__":
    run()


# @app.command()
# def source(action: str, conn_uri: str, name: Optional[str] = None):
#     if action == "create":
#         try:
#             source = rc.create_datasource(conn_uri, name)
#         except Exception as e:
#             console.print(f"Error: {e}")
#             return

#         console.print(f'Added ⛁ Datasource "[green]{source.name}[/green]"')
#     elif action == "list":
#         sources = rc.get_sources()
#         if len(sources) == 0:
#             console.print("No datasources found")
#         else:
#             for source in sources:
#                 console.print(f"  - [green]{source.name}[/green]")
#     else:
#         console.print(f"Unknown action: {action}")


# @app.command()
# def layer(action: str, name: str):
#     if action == "build":
#         console = Console()

#         layout = Layout()
#         layout.split_row(Layout(name="chat", ratio=3), Layout(name="json", ratio=2))
#         layout["chat"].split_column(
#             Layout(name="chat_history"), Layout(name="chat_input", size=3)
#         )

#         chat_history = [
#             (
#                 "User",
#                 "Users will want to ask questions like 'Which purchases on my credit card contributed the most points?' and 'When was that transaction?'",
#             ),
#             (
#                 "AI",
#                 "Got it! I've made a metric called [green bold on black]`points_transaction`[/green bold on black] using the DDL with dimensions [green bold on black]`points`[/green bold on black], [green bold on black]`user_id`[/green bold on black], and [green bold on black]`transaction_date`[/green bold on black]",
#             ),
#             (
#                 "User",
#                 "They'll also want to know what categories earned them the most points.",
#             ),
#             (
#                 "AI",
#                 "I've added a dimension [green bold on black]`category`[/green bold on black] to the [green bold on black]`points_transaction`[/green bold on black] metric and joined on the table [green bold on black]`vendors`[/green bold on black] to do so.",
#             ),
#         ]

#         from relta.semantic.base import Metric, Dimension, Measure

#         metric = Metric(
#             name="points_transaction",
#             datasource="card_users",
#             dimensions=[
#                 Dimension(name="points", description="Points earned from transaction"),
#                 Dimension(
#                     name="transaction_date", description="Date of the transaction"
#                 ),
#                 Dimension(name="user_id", description="User ID"),
#                 Dimension(name="category", description="Category of the transaction"),
#             ],
#             measures=[
#                 Measure(
#                     name="total_points",
#                     description="Points earned from transactions",
#                     agg_operation="SUM",
#                     expr="points",
#                 )
#             ],
#             sample_questions=[
#                 "Which purchases on my credit card contributed the most points?",
#                 "How many points did I earn last month?",
#             ],
#             description="Points earned from transactions",
#             sql_to_underlying_datasource="SELECT t.rewards as points, t.date as transaction_date, v.category as category FROM transactions t JOIN vendors v ON t.vendor_id = v.id",
#         )

#         def create_chat_table():
#             table = Table(
#                 show_header=False,
#                 expand=True,
#                 highlight=True,
#                 # row_styles=["dim", ""],
#                 # show_lines=False,
#                 # show_edge=False,
#                 box=None,
#             )
#             table.add_column("AI", style="green")
#             table.add_column("User", style="cyan", justify="right")
#             for role, message in chat_history:
#                 # wrapped_msg = textwrap.fill(message, width=40)
#                 if role == "User":
#                     table.add_row("", Text(message))
#                 else:  # AI message
#                     table.add_row(Text.from_markup(message), "")
#             return table

#         chat_table = create_chat_table()
#         formatted_json = Syntax(
#             metric.model_dump_json(indent=2),
#             "json",
#             # theme="dracula",
#             # line_numbers=True,
#             # word_wrap=True,
#         )

#         layout["chat_history"].update(Panel(chat_table, title="Chat"))
#         layout["json"].update(
#             Panel(formatted_json, title="Metrics", width=80, expand=True)
#         )
#         chat_input = Text("> ", style="bold cyan")
#         layout["chat_input"].update(Panel(chat_input, title="", border_style="cyan"))

#         console.print(layout)
