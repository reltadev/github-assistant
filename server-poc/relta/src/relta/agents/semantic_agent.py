from typing import Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, AnyMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.prompts import ChatPromptTemplate
from ..semantic.base import SemanticLayerContainer
from ..semantic.semantic_layer import SemanticLayer
from ..datasource import DataSource
from langchain_core.messages import HumanMessage
import time

# from langgraph.checkpoint.sqlite import SqliteSaver
# from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

GENERATE_PROMPT = """
You are an expert data modeler and data scientist specializing in semantic layer development and data modeling. Your role is to help technical users iterate on semantic layers for their data.

### Definitions:
- A semantic layer is a collection of SQL views (called metrics) that would answer those questions and abstract away unnecessary details. 
- A metric is a named set of dimensions and measures that can be used to answer a question. It is a SQL view.
- Dimensions are like columns in a view -- they can be used to group or filter data.
- Measures are aggregate operations on dimensions -- they can be used to calculate sums, averages, counts etc.

### Task
Given a user's statement in context with the chat history, the semantic layer, and the datasource DDL,
try to make a change to the semantic layer that accounts for the user's statement or give the user information they requested. 
This will be in a JSON format provided below. You will be providing reasoning for changes as well.

Let's think step by step.
First, determine if the user is proposing a list of questions to support.
If the user is proposing questions to support, then:
1. You should understand the business questions and what the underlying data they are asking for.
2. Group the questions into metrics where the questions differ by a choice of GROUP BY, WHERE, HAVING, LIMIT, etc. clauses. They should retain the same "internal structure" about the information they are asking for.
3. You should look at the DDL to find the underlying tables and columns that are needed for the metric. Consider the description and the columns provided. You may need to join tables to get all the relevant columns you need or include subqueries to get the correct data.

Else, 
1. Understand the user's statement and the chat history in context with the current semantic layer.
2. Determine if the user's statement requires a new dimension, measure, or metric. You should first look at the DDL to determine what you can do.
   If you need clarification on what to do, ask the user for clarification.
3. Apply the changes to the semantic layer. You may also be deleting a metric, dimension, or measure, depending on chat history.


### Guidelines
- You must provide an itemized list of changes you are making to the semantic layer and the reasoning behind them in the `update_reasoning` field. This includes changes to existing metrics/dimensions/measures/examples, renaming them, adding new ones, etc.
- You may be working on the proposed update to the semantic layer, which you can tell by the presence of a `update_reasoning` field in the current semantic layer.
  In that case, if you make an update, you should use the previous reasoning as a starting point for your reasoning of further changes.
- If the statement does not need a change to the semantic layer, just return the current semantic layer.
- You should try to make metrics general, so they can cover multiple business questions on the same metric, but they should remain precise to tracking a single business metric.
- If you can expand the scope of a metric to cover multiple questions, you should do so, as long as the metric stays precise.
- Every question that is a business question must match to a metric.
- The datasource should always be set to "{DATASOURCE_NAME}".
- Data scientists will be able to GROUP BY and filter on any dimension you provide and will be able to filter on any measure you provide. 
- The `sql_to_underlying_datasource` field should be a "SELECT" statement that you would put into a "CREATE VIEW" statement. It should have every dimension in the metric defined as a column in the view. 
  The measures, as aggregate operations, should not be defined in this statement, and there should not be any "GROUP BY" statements based on a dimension in the SQL statement. 
  The view name should be the same as the metric. If tables need to be joined to create the view, you should join them.
- Any columns or dimensions that are used in a measure for a metric need to be included as dimensions in the metric. 
  You should not have a measure reference a column directly in the view -- make that column a dimension and then use it.
- The dialect of SQL you should use is PostgreSQL for creating views and for the aggregate operation used in measures.
- You should label dimensions with semantic information not captured by the name or datatype -- for example, if `country` is a column defined as VARCHAR(255) in the database but you receive a comment that it is a 2 digit country code, you should write that in the description of the corresponding dimension.
- You should not use the name "examples" or any capitalization variation for any metric, as it is reserved for another file.

---
Current Semantic Layer:
{SEMANTIC_LAYER_REPR}

Datasource DDL:
{DATASOURCE_DDL}
"""

RESPONSE_PROMPT = """
Using the itemized list of changes (the `update_reasoning` field in the JSON data provided below) and the chat history, write a brief response to the user (<100 words), who is technical and knows SQL.
You should briefly describe new changes to the semantic layer like dimensions, measures, metrics, and examples. You should not cover the sample questions.

---

{curr_update}
"""


class SemanticLayerUpdate(BaseModel):
    semantic_layer: SemanticLayerContainer = Field(
        description="The semantic layer with updates applied."
    )
    # response: str = Field(
    #     description="A response to the end user for their statement. If there are updates to the metrics, briefly describe each change."
    # )


class State(BaseModel):
    # model_config = ConfigDict(arbitrary_types_allowed=True)
    messages: Annotated[list[AnyMessage], add_messages] = []
    source: DataSource
    curr_update: Optional[SemanticLayerUpdate] = None


class SemanticAgent:
    model = ChatOpenAI(model="gpt-4o", temperature=0)
    model_small = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    @staticmethod
    async def generate_update(state: State):
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", GENERATE_PROMPT), ("placeholder", "{messages}")]
        )
        chain = prompt_template | SemanticAgent.model.with_structured_output(
            SemanticLayerUpdate
        )
        layer_update: SemanticLayerUpdate = await chain.ainvoke(
            {
                "messages": state.messages,
                # "SEMANTIC_LAYER_MODEL": json.dumps(
                #     SemanticLayerUpdate.model_json_schema(mode="serialization"),
                #     indent=2,
                # ),
                "SEMANTIC_LAYER_REPR": state.source.semantic_layer.dumps(),
                "DATASOURCE_DDL": state.source._get_ddl(),
                "DATASOURCE_NAME": state.source.name,
            }
        )

        return {
            "curr_update": layer_update,
            # "messages": [AIMessage(content=layer_update.response)],
        }

    @staticmethod
    async def respond(state: State):
        prompt_template = ChatPromptTemplate.from_messages(
            [("system", RESPONSE_PROMPT), ("placeholder", "{messages}")]
        )
        chain = prompt_template | SemanticAgent.model_small
        res = await chain.ainvoke(
            {"messages": state.messages, "curr_update": state.curr_update}
        )
        return {"messages": [res]}

    def __init__(self):
        # self.checkpointer = SqliteSaver(
        #     sqlite3.connect(
        #         Configuration().semantic_memory_path, check_same_thread=False
        #     )
        # )
        self.checkpointer = MemorySaver()
        self.graph_builder = StateGraph(State)
        self.graph_builder.add_node("generate_update", SemanticAgent.generate_update)
        self.graph_builder.add_node("respond", SemanticAgent.respond)
        self.graph_builder.add_edge(START, "generate_update")
        self.graph_builder.add_edge("generate_update", "respond")
        self.graph_builder.add_edge("respond", END)

        self.graph = self.graph_builder.compile(checkpointer=self.checkpointer)

    def invoke(
        self,
        message: str,
        layer: SemanticLayer,
        thread_id: Optional[int] = None,
    ):
        """Invoke the semantic agent on a message. Each layer has one single thread, defined by the datasource id.

        Args:
            message (str): The latest message to invoke the semantic agent on.
            layer (SemanticLayer): The semantic layer to invoke the semantic agent on.
            thread_id (Optional[int]): The thread id to use for the semantic agent. If None, a new thread id will be generated.
        Returns:
            StateDict: The state of the semantic agent after invoking it, as a dictionary.
        """
        state = State(
            messages=[HumanMessage(content=message)],
            source=layer.datasource,
            curr_update=None,
        )
        if thread_id is None:
            thread_id = int(time.time())
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.invoke(state, config=config)

    async def ainvoke(
        self,
        message: str,
        layer: SemanticLayer,
        thread_id: Optional[int] = None,
    ):
        """Async invoke the semantic agent on a message. Each layer has one single thread, defined by the datasource id.

        Args:
            message (str): The latest message to invoke the semantic agent on.
            layer (SemanticLayer): The semantic layer to invoke the semantic agent on.
            thread_id (Optional[int]): The thread id to use for the semantic agent. If None, a new thread id will be generated.
        Returns:
            StateDict: The state of the semantic agent after invoking it, as a dictionary.
        """
        state = State(
            messages=[HumanMessage(content=message)],
            source=layer.datasource,
            curr_update=None,
        )
        if thread_id is None:
            thread_id = int(time.time())
        config = {"configurable": {"thread_id": thread_id}}
        return await self.graph.ainvoke(state, config=config)
