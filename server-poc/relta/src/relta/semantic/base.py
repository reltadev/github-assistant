from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from langchain_core.messages import AnyMessage


class Measure(BaseModel):
    """A measure for a metric.

    This is similar to a measure in LookML -- it is an aggregate operation on some dimensions.
    For example, a measure could be the sum of a column or the average of columnA * columnB.
    """

    name: str = Field(
        description="A short name of the measure. Must be unique within the metric."
    )
    description: str = Field(
        description="A longer description of the measure. Keep it within 3 sentences."
    )
    expr: str = Field(
        description="The SQL expression for this aggregate operation. This must be a valid PostgreSQL expression. Any columns used should also be defined as dimensions."
    )

    # agg_operation: str = Field(
    #     description="The aggregate operation the measure does. This must be a supported aggregation function in the PostgreSQL SQL Dialect. For example, 'SUM', 'AVG', 'COUNT'."
    # )
    # expr: str = Field(
    #     description="The argument to the aggregate operation. Must be a valid SQL expression in the PostgreSQL dialect. If you are using a column, it must be a defined dimension."
    # )


class Dimension(BaseModel):
    """A dimension for a metric.

    This is similar to a dimension in LookML -- it can be used to group or filter data in a metric.
    For example, a dimension could be a column in a table or a calculation based on columns in a table.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(
        description="A short name of the dimension. Must be unique within the metric. It can be the same as the column name."
    )

    description: str = Field(
        description="A longer description of the dimension. Keep it within 3 sentences."
    )

    categories: Optional[list] = Field(
        description="The categories of the dimension. This is used to create a list of values for the dimension. This should not be filled out when setting up the semantic layer."
    )

    dtype: Optional[str] = Field(description="The data type of the dimension.")


class Metric(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = Field(
        description="A short name of the metric. Must be unique within the semantic model. Use snake case."
    )
    description: str = Field(
        description="A longer description of the metric. Keep it within 3 sentences."
    )
    datasource: str = Field(
        description="The name of the DataSource the metric is based on. This must be a valid DataSource in the semantic model."
    )
    dimensions: list[Dimension] = Field(
        description="The dimensions of the metric. These are used to group or filter the data in the metric."
    )
    measures: list[Measure] = Field(
        description="The measures of the metric. These are the aggregate operations on the dimensions."
    )
    sample_questions: list[str] = Field(
        description="Sample natural language questions that this metric answers."
    )
    sql_to_underlying_datasource: str = Field(
        description="The SQL that is used to calculate the metric from the underlying data source. This will be used to create a view for this metric. Tables and columns in this SQL should be fully formatted as databasename.schemaname.tablename.columnname"
    )


class ProposedMetrics(BaseModel):
    question_observations: list[str] = Field(
        description="Observations on business questions about what it could tell us about metrics needed"
    )
    step_thinking: list[str] = Field(
        description="The step by step thinking that led to the metrics"
    )
    metrics: list[Metric] = Field(
        description="A list of metrics that are proposed based on the question observations"
    )
    num_questions: int = Field(
        description="The number of questions that were used to generate the metrics"
    )


class UpdatedMetric(BaseModel):
    original_name: str = Field(
        description="The original name of the metric. If this is a new metric, use the new metric name."
    )
    updated_metric: Metric = Field(description="The updated metric.")


class RefinedMetrics(BaseModel):
    observation: list[str] = Field(
        description="Observations made for each piece of feedback."
    )
    metrics: list[UpdatedMetric] = Field(
        description="New or updated metrics. If a metric is not updated, do not return it."
    )


class Feedback(BaseModel):
    sentiment: Literal["positive", "negative"] = Field(
        description="The sentiment of the feedback."
    )
    reason: Optional[str] = Field(description="The reason for the feedback.")
    selected_response: AnyMessage = Field(
        description="The response that the user selected."
    )
    message_history: list[AnyMessage] = Field(description="The message history.")


class Example(BaseModel):
    prompt: str = Field(description="The prompt for the example.")
    sql: str = Field(description="The SQL query for the example.")
    explanation: str = Field(description="The explanation for the example.")


# class MetricCollection(BaseModel):
#     """Used for dumping just metrics."""
#     metrics: list[Metric] = Field(description="A list of metrics.")


class ExampleCollection(BaseModel):
    """Used for persistence (load/dump) of examples."""

    examples: list[Example] = Field(description="A collection of examples.")


# consider splitting into two but not important rn
# Serves two purposes: dumping to a string and as both an input & output schema to the semantic agent
class SemanticLayerContainer(BaseModel):
    metrics: list[Metric] = Field(
        description="A collection of metrics. If you are updating the semantic layer, you should apply the changes to metrics here and reproduce any that haven't changed."
    )
    examples: list[Example] = Field(
        description="A collection of examples. If you are updating the semantic layer, you should apply the changes to examples here and reproduce any that haven't changed."
    )
    update_reasoning: str = Field(
        description="""An itemized list of changes made to the semantic model metrics and examples and the reasoning behind why. 
        This is used to generate a response to the user describing the diff."""
    )
