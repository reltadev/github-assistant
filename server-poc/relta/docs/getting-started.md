# Getting Started

We'll walk through setting up an AI Assistant that can answer questions about flights. 

!!! warning "Single-tenant Example"
    For simplicity, every user has access to all rows in this example. A later tutorial will cover supporting multi-tenant setups.
    Please reach out [to us here](https://www.relta.dev/#:~:text=the%20semantic%20layer.-,Get%20in%20touch,-Name) if you'd like to use Relta in a multi-tenant setup -- we'd love to chat!

!!! info "Data we're using"
    We're using a dataset of flights from the query language [Malloy's data examples](https://github.com/malloydata/malloy-samples/tree/main/data).
    We've loaded `flights.parquet`, `airlines.parquet`, and `airports.parquet` into a Postgres database.
    <!-- todo: head of the data -->

Relta exposes a CLI around the Python library for easier set up. 
However, you can use the library to set up, shown in tabs. 
We will use both the CLI and library in this tutorial.

## Connect to a database

Relta currently supports connecting to DuckDB, PostgreSQL databases and CSV files. You can use the CLI to add the data source to Relta:

=== "CLI"
    <!-- termynal -->
    ```bash
    $ relta create $PG_FLIGHTS_DSN --name flights
    Connected to ⛁ DataSource, assigned name "flights"
    ```

=== "Library"
    ```python
    import os
    import relta
    rc = relta.Client()
    source = rc.create_datasource(os.environ["PG_FLIGHTS_DSN"], name="flights")
    ```

Notice the term "DataSource" -- this is the representation of a database in Relta. This is one of the central objects in Relta.

## Define Semantic Layer

The semantic layer controls the set of metrics that Relta will answer questions from. 
Relta does not generate SQL for any other metrics that it is asked about. Better yet, the semantic layer is just JSON, so you can edit it yourself!

You can set it up by providing the natural language questions that you want answered with optional context about the data source:

=== "CLI"
    <!-- termynal -->
    ```bash
    $ relta propose flights
    Enter in business context for the datasource: 
    Enter user questions to support. Type 'done' when finished.
    $ On average, how long is a Southwest/American/etc. flight delayed?
    $ What are the top 5/10/etc. most flown routes?
    $ Give me the names of airlines most commonly out of SFO/LAX/etc.
    $ done
    Semantic layer proposal complete. See 'relta layer' to view.
    ```

=== "Library"
    ```python
    import relta

    rc = relta.Client()
    source = rc.get_datasource("flights")
    source.semantic_layer.propose(
        queries=[
            "On average, how long is a Southwest/American/etc. flight delayed?",
            "What are the top 5/10/etc. most flown routes?",
            "Give me the names of airlines most commonly out of SFO/LAX/etc.",
        ],
    )
    ```

An example of a metric from this is:

```json
{
  "name": "most_frequent_airlines_by_airport",
  "description": "This metric identifies airlines that have the highest number of departures from specific airports. It helps in understanding airline activity at different airports.",
  "datasource": "flights",
  "dimensions": [
    {
      "name": "origin",
      "description": "The code of the airport from which the flight departs. This is used to filter flights by departure airport.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "carrier",
      "description": "The code of the airline operating the flight. This is used to identify the airline for which the departure count is being calculated.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "name",
      "description": "The full name of the airline. This is used to provide a human-readable name for the airline.",
      "categories": null,
      "dtype": "VARCHAR"
    }
  ],
  "measures": [
    {
      "name": "departure_count",
      "description": "The total number of flights departing from the airport by the airline. This is calculated as the count of flight records for each airline and airport.",
      "expr": "COUNT(flight_num)"
    }
  ],
  "sample_questions": [
    "Give me the names of airlines that fly most often out of SFO.",
    "Which airlines have the most departures from OAK?"
  ],
  "sql_to_underlying_datasource": "SELECT flights.origin, flights.carrier, carriers.name, flights.flight_num FROM public.flights JOIN public.carriers ON flights.carrier = carriers.code"
}
```

Let's say that we want the full name of the airport accessible to Relta. Let's add this to the semantic layer manually by adding a dimension and extracting it from the SQL with an extra JOIN:

```json hl_lines="6-11 42"
{
  "name": "most_frequent_airlines_by_airport",
  "description": "This metric identifies airlines that have the highest number of departures from specific airports. It helps in understanding airline activity at different airports.",
  "datasource": "flights",
  "dimensions": [
    {
      "name": "origin_name",
      "description": "The full name of the airport from which the flight departs. This is used to filter flights by departure airport.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "origin",
      "description": "The code of the airport from which the flight departs. This is used to filter flights by departure airport.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "carrier",
      "description": "The code of the airline operating the flight. This is used to identify the airline for which the departure count is being calculated.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "name",
      "description": "The full name of the airline. This is used to provide a human-readable name for the airline.",
      "categories": null,
      "dtype": "VARCHAR"
    }
  ],
  "measures": [
    {
      "name": "departure_count",
      "description": "The total number of flights departing from the airport by the airline. This is calculated as the count of flight records for each airline and airport.",
      "expr": "COUNT(flight_num)"
    }
  ],
  "sample_questions": [
    "Give me the names of airlines that fly most often out of SFO.",
    "Which airlines have the most departures from OAK?"
  ],
  "sql_to_underlying_datasource": "SELECT airports.name as origin_name, flights.origin, flights.carrier, carriers.name, flights.flight_num FROM public.flights JOIN public.carriers ON flights.carrier = carriers.code JOIN public.airports ON flights.origin = airports.code"
}
```


To edit the semantic layer, you can manually edit the JSON or programmatically edit it with the library.

## Deploy Relta

Relta is designed to run in separate Python processes per user to provide isolated databases. 
However, in this case, all users have access to all rows in the database. so we can have all users query the same replica. Let's then use Relta in a standard API to chat with that single replica.

Let's first create the replica database that all users will query. This operation is called "deploying" the semantic layer on the DataSource.
=== "CLI"
    <!-- termynal -->
    ```bash
    $ relta deploy flights
    Semantic layer for flights has been deployed successfully.
    ```

=== "Library"
    ```python
    import relta

    rc = relta.Client()
    source = rc.get_datasource("flights")
    source.deploy()
    ```

!!! info "Is this expensive?"
    Relta will only pull the tables that are needed for the semantic layer, and in a multi-tenant setup, within those tables only the rows accessible by that user.

### Your first chat with Relta

Before we get to the API, it might be useful to preview what chatting with Relta is like. You can use the CLI to chat with the data source:

```bash
$ relta chat flights
Exit chat with 'exit', 'quit', or 'q'
$ which carrier flies out of LAX the most?
AI: The carrier that flies out of LAX the most is Southwest Airlines, with a total of 4,282 departures.
```

### Using Relta in an API

Now, we can set up a simple API using [FastAPI](https://fastapi.tiangolo.com/):

```python
import relta
from fastapi import FastAPI

rc, app = relta.Client(), FastAPI()

@app.post("/chat")
def create_chat(datasource: str) -> int:
    source = rc.get_datasource(datasource)
    return rc.create_chat(source).id

@app.post("/chat/{chat_id}/prompt")
def prompt_chat(chat_id: int, question: str) -> (int, str):
    resp = rc.get_chat(chat_id).prompt(question)
    return (resp.index, resp.text)
```
<!-- TODO: consider example with full state if that is the expected output. -->

We can run this API with FastAPI:

```bash
$ fastapi dev server.py
```


## Refine Semantic Layer with feedback
One of the most powerful features of Relta is automatically handling user feedback to improve the semantic layer. When Relta receives feedback, it will automatically raise a PR on the GitHub repository it is hosted from that modifies the semantic layer.

Let's add an endpoint to the API for this feedback:
```python
# ...
@app.post("/chat/{chat_id}/resp/{resp_id}/feedback")
def feedback(chat_id: int, resp_id: int, sentiment: Literal["positive", "negative"], feedback: str) -> None:
    chat = rc.get_chat(chat_id)
    chat.responses[resp_id].feedback(sentiment, feedback)
    chat.datasource.semantic_layer.refine(pr=True)
# ...
```

<!-- NOTE: this code block might not work!
chat = rc.get_chat(chat_id)
chat.responses[resp_id].feedback(sentiment, feedback)
source = rc.get_datasource(chat.datasource.name)
source.semantic_layer.refine(pr=True)

source might be a diff object than chat.source, and especially source.semantic_layer could be a diff object than chat.datasource.semantic_layer
look for better ways to do the refinement code -->




<!-- ## Sample Frontend with assistant-ui -->
<!-- TODO: Full Code -->