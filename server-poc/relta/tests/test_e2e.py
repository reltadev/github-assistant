from dotenv import load_dotenv
import relta
import os
from pathlib import Path
from typer.testing import CliRunner

load_dotenv(verbose=True)


# Adding files should be reflected in .github/workflows/pytest.yml
SAMPLE_DATA_FILE_PATH = str(Path(os.environ["SAMPLE_DATA_PATH"]) / "data.csv")
PG_CONNECTION_URI = os.environ["PG_CONNECTION_URI"]
DUCKDB_FILE_PATH = os.environ["DUCKDB_FILE_PATH"]


# == E2E Tests ==
def test_csv_connection():
    rc = relta.Client()
    source = rc.create_datasource(SAMPLE_DATA_FILE_PATH)
    assert source.name == "data"

    source = None
    source = rc.get_datasource(name="data")
    assert source.name == "data"

    rc.delete_datasource("data")


def test_pg_connection():
    rc = relta.Client()
    source = rc.get_or_create_datasource(name="imdb", connection_uri=PG_CONNECTION_URI)

    assert source.name == "imdb"

    rc.delete_datasource("imdb")


def test_creating_csv_connection_with_same_name():
    rc = relta.Client()
    rc.create_datasource(SAMPLE_DATA_FILE_PATH)
    try:
        rc.create_datasource(SAMPLE_DATA_FILE_PATH)
        raise Exception(
            "Should have thrown a CatalogException as a connection with same name exists"
        )
    except relta.DuplicateResourceException:
        pass

    datasource2 = rc.create_datasource(SAMPLE_DATA_FILE_PATH, name="data2")
    assert datasource2.name == "data2"

    rc.delete_datasource("data")
    rc.delete_datasource("data2")


def test_duckdb():
    rc = relta.Client()
    source = rc.create_datasource(DUCKDB_FILE_PATH, name="github_data")
    layer = source.semantic_layer
    layer.propose(["how many stars does the repo have?"])
    layer.dump()
    source.deploy()
    rc.delete_datasource("github_data")


def test_simple_e2e():
    rc = relta.Client()
    source = rc.create_datasource(SAMPLE_DATA_FILE_PATH, name="data")
    layer = source.semantic_layer
    layer.propose(
        [
            "how many days on average did it take for work-orders to be completed?",
            "which work order takes longest to complete?",
        ]
    )
    layer.dump()
    source.deploy()
    chat = rc.create_chat(source)
    resp = chat.prompt("how long did plumbing take?")
    resp.feedback("negative", "I think the answer is 10 days")
    layer.refine()
    rc.delete_datasource("data")


def test_cli_create():
    from relta.cli.typer_cli import app

    runner = CliRunner()
    res = runner.invoke(app, ["create", SAMPLE_DATA_FILE_PATH, "--name", "data"])
    assert res.exit_code == 0

    res = runner.invoke(app, ["delete", "data"])
    assert res.exit_code == 0
