# DataSource

A `DataSource` object in Relta has the following roles and responsibilities:

1. It manages the connection to the external datasource
2. It maintains a `SemanticLayer` object
3. It creates a local transient database from the external datasource that matches it's semantic layer

We support connecting to PostgreSQL, DuckDB, MySQL, CSV, and Parquet datasources.

In the set up of Relta, you will set up your DataSource's external connections (1) and their semantic layers (2).
When deploying Relta, you will read in those persisted DataSources and create their local databases, usually limiting it to the current user you are serving (3).

The "local transient database" is intended to provide two benefits:

1. Each user receives a sandboxed database with only the data they are allowed to access. _The LLM cannot mix user's data when running a query, because it isn't there_.
2. No LLM-produced SQL is ran against your production database -- this prevents long-running queries from locking up your database.

!!! info "More on the local database"
    Under the hood, we use [DuckDB](https://duckdb.org/) to create the local database. It runs fully in process, allowing for fast query times.

## Usage

Setting up a DataSource can be done directly with the library or through the CLI. Using the CLI for this is the recommended approach and is covered in the [Getting Started](../getting-started.md) guide. We will show how to do this with the library, as the same functions are also used when deploying Relta.

You should create a DataSource through `create_datasource` method in the Relta Client. This persists the DataSource to your repository. There are also `get_datasource` and `get_or_create_datasource` methods for accessing existing DataSource objects.

```python
import relta
rc = relta.Client()
source = rc.create_datasource("data/invoices.csv", name="week_invoice")
```

!!! warning "Don't duplicate DataSources in the same Python process"
    Getting multiple copies of the same DataSource (e.g. by creating one and getting it right after) and assigning them to different variables will create two separate objects in memory. As they have separate semantic layer objects, this can cause unexpected behavior.
    ```python
    ### DON'T DO THIS ###
    source_original = rc.create_datasource("data/invoices.csv", name="week_invoice")
    source_copy = rc.get_datasource("week_invoice")

    ### THIS IS OK ###
    source = rc.create_datasource("data/invoices.csv", name="week_invoice")
    source = rc.get_datasource("week_invoice")
    ```


Accessing a DataSource's semantic layer can be done through the `semantic_layer` property. This is usually only done to be able to setup the semantic layer.

```python hl_lines="3 4"
import relta
rc = relta.Client()
source = rc.get_datasource(name="week_invoice")
source.semantic_layer.propose("How many times did Alice make a payment?")
```

When you are deploying Relta, you should already have a set up semantic layer in your repository, so accessing the semantic layer is not necessary.

To pull in data from the external datasource once a semantic layer is set up, you can use the `deploy` method, which will create the local transient database.

```python hl_lines="4 5 6"
import relta
rc = relta.Client()
source = rc.get_datasource(name="week_invoice")
print(source.semantic_layer.metrics) # this is automatically loaded in when you get the datasource
source.deploy()
```

We refer to this as deploying the semantic layer on the database. Once this is complete, you can create `Chat`s on this DataSource and begin running queries.

```python hl_lines="6-8"
import relta
rc = relta.Client()
source = rc.get_datasource(name="week_invoice")
source.deploy()

chat = rc.create_chat(source)
resp = chat.prompt("How many times did Omar pay")
print(resp.text)
```

## API Reference

::: relta.DataSource
    options:
        show_root_toc_entry: false
