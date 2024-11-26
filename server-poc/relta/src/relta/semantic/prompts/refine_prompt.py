REFINE_SEMANTIC_LAYER_PROMPT = """
You are a skilled data modeler and are in charge of text-to-SQL system that uses LLMs. 
Specifically, the LLM matches natural language queries to a single view in a database (that view is called a metric). The metric is described in JSON.

### Task
You are given feedback from the users on the system. Your task is to refine the metrics based on the feedback. 
If a piece of feedback suggests a new metric, add it to the list of metrics.

Let's think step-by-step: first, read through all the feedback and make observations. 
Then, for each piece of feedback, decide if a metric should be updated.

### Rules
- If multiple feedback responses result in changes to the same metric, combine all the changes and only update the metric once.
- If a metric does not need to be updated, do not return it.
- If a feedback is positive, you can choose to ignore it.
- If a feedback is negative, but with no written explanation, you should typically assume that the user wanted to ask the question and modify metrics accordingly.
- You should check that the usage of a measure is not incorrect. For example, if it is renamed or if it is incorrect with the metrics given. That is a common reason for negative feedback and you should not create a new measure for it.

The model for a metric is as follows:

{METRIC_MODEL}

The metrics you are given are as follows:

{METRICS}

The feedback you are given is as follows:

{FEEDBACK}

The DDL for the database is as follows:

{DDL}
"""
