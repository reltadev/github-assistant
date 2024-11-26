# Semantic Layer

A `SemanticLayer` object in Relta represents the _metrics_ that users can ask questions about per `DataSource`.

## Structure

A metric can be thought of a SQL View on the tables of the `DataSource`. A definition of a metric contains dimensions, which represent columns of the view, and measures, which represents the aggregate functions that can be applied to the dimensions.

An example of a metric is:

```json
{
  "name": "carrier_route_analysis",
  "description": "This metric provides the count of routes per carrier and identifies the most popular route for each carrier.",
  "datasource": "db",
  "dimensions": [
    {
      "name": "carrier",
      "description": "The code of the carrier operating the flight.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "carrier_name",
      "description": "The full name of the carrier.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "origin",
      "description": "The origin airport code for the flight.",
      "categories": null,
      "dtype": "VARCHAR"
    },
    {
      "name": "destination",
      "description": "The destination airport code for the flight.",
      "categories": null,
      "dtype": "VARCHAR"
    }
  ],
  "measures": [
    {
      "name": "route_count",
      "description": "The total number of routes flown by the carrier.",
      "expr": "COUNT(DISTINCT origin || '-' || destination)"
    }
  ],
  "sample_questions": [
    "Give me the full names of the top 5 carriers that flew the most routes and what their most popular route is."
  ],
  "sql_to_underlying_datasource": "SELECT f.carrier, c.name AS carrier_name, f.origin, f.destination FROM public.flights f JOIN public.carriers c ON f.carrier = c.code"
}
```

The `sql_to_underlying_datasource` field is the `SELECT` statement that is in a `CREATE VIEW` statement and can contain arbitrary DDL.

The SQL Agent is given the `SemanticLayer` which contains a list of metrics, and the SQL Agent only uses dimensions and measures that are defined in the `SemanticLayer`.

An example of SQL generated from that metric is:

```sql
-- What airline flies the least routes?
SELECT carrier_name,
       COUNT(DISTINCT origin || '-' || destination) as route_count
FROM   common_routes
GROUP BY carrier_name
ORDER BY route_count ASC LIMIT 1;
```

Observe that the SQL Agent only uses the dimensions and measures that are defined in the metric, and the metric itself is the view that we pull data from. In fact, the SQL Agent does not have access to the original tables or columns, nor even the create view statement to generate a view -- it only has the dimensions and measures for the metric. **So the SQL Agent cannot work with any data not declared in the metric.**

## Usage

A `SemanticLayer` object is automatically created when a `DataSource` object is created (either by getting a `DataSource` from disk or creating a new one). It is accessible from the `semantic_layer` property of a `DataSource`.

By default, the `SemanticLayer` automatically loads in metrics that have been previously defined in it's directory, which is by default `.relta/semantic_layer/{datasource_name}`.

```python
import relta

rc = relta.Client()
source = rc.get_datasource("flights")
print(source.semantic_layer.metrics) # {name: "most_frequent_airlines_by_airport", ...}
```

To generate metrics from scratch for a semantic layer, you can use the `propose` method. We cover how to do this using the CLI in the [Getting Started](../getting-started.md) but present it using library code here. Observe that we are only passing in natural language questions, and optionally business context, to the `propose` method.

```python
import relta

rc = relta.Client()
source = rc.create_datasource(os.environ["PG_AIRPORTS_DSN"], "airports")
source.semantic_layer.propose([
    "Which airport has the longest security line?",
    "Which airports have CLEAR?",
    "Which airport should I go to if I'm flying to LA from NY, if I want to avoid cost?"
])
```

If you want to edit a metric, you can do it programmatically or by editing the JSON file.

<!-- ```python
import relta

rc = relta.Client()
metrics = rc.get_datasource("airports").semantic_layer.metrics

metrics = layer.metrics
metrics["carrier_route_analysis"].description = "This metric provides the count of routes per carrier and identifies the most popular route for each carrier."

``` -->

### Refining Metrics

If a user gives feedback on a metric, the relevant `Response` is added to the `feedback_responses` list of the `SemanticLayer`, which you can then call `refine` on to suggest updates to the Semantic Layer:

```python
import relta

rc = relta.Client()
source = rc.get_datasource("airports")

chat = rc.create_chat(source)
resp = chat.prompt("which airport is the biggest?")
resp.feedback("negative", "please add support for airport size and passenger volume")

source.semantic_layer.refine(pr=True)
```

`pr=True` will automatically raise a PR with the changes, given your Configuration includes the optional `GITHUB_*` variables.

<!-- !!! warning "Feedback is not persisted"
    Currently, feedback from a user is only stored in memory and not saved onto disk with the `SemanticLayer`. -->

## API Reference

::: relta.SemanticLayer
    options:
        show_root_toc_entry: false

::: relta.semantic.base
    options:
        show_root_toc_entry: false