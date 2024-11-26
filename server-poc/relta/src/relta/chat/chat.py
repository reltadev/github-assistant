from __future__ import annotations
from typing import Optional, ClassVar, Literal
from sqlmodel import SQLModel, Field, Relationship, Sequence
from pydantic import ConfigDict

# from .response import Response
# from pydantic.dataclasses import dataclass
from dataclasses import dataclass
from ..datasource import DataSource
from ..agents import SQLAgent
from langchain_core.messages import AnyMessage
import logfire


# TODO consider making a BaseModel to back Response and getting it as the output from the LLM ... but could it hallucinate sql and sql_result?
# TODO: think about using @property for read-only getters.
@dataclass
class Response:
    chat: Chat
    message: AnyMessage
    id: int
    text: str
    feedback_sentiment: Optional[Literal["positive", "negative"]] = None
    feedback_reason: Optional[str] = None
    sql: Optional[str] = None
    sql_result: Optional[dict] = None

    def feedback(
        self,
        sentiment: Literal["positive", "negative"],
        reason: Optional[str] = None,
    ):
        self.feedback_sentiment = sentiment
        self.feedback_reason = reason

        self.chat.datasource.semantic_layer.feedback_responses.append(self)


chat_id_seq = Sequence("chat_id_seq", metadata=SQLModel.metadata)


class Chat(SQLModel, table=True):
    """A Thread of conversation.

    Contains metadata around a thread and exposes simple calls to the agent.
    """

    model_config = ConfigDict(extra="allow")

    id: Optional[int] = Field(default=chat_id_seq.next_value(), primary_key=True)

    datasource_id: int = Field(foreign_key="datasource.id")
    datasource: DataSource = Relationship(back_populates="chats")
    # _config: Configuration  # set by Client when this is created (or loaded) # why does this not work?

    agent: ClassVar[SQLAgent]  # populated when a Client is initialized.
    _responses: list["Response"]  # populated when a Client is initialized.

    @property
    def responses(self) -> list[Response]:
        if self._responses is None:
            self._responses = []
        return self._responses

    def _get_messages(self) -> list[AnyMessage]:
        checkpoint = self.agent.checkpointer.get(
            {"configurable": {"thread_id": self.id}}
        )
        return checkpoint["channel_values"]["messages"]

    def prompt(self, s: str, debug=False, only_sql: bool = False, **kwargs) -> Response:
        """Ask a question on the thread.

        Args:
            s (str): question
            debug (bool, optional): If True, runs the graph in debug mode. If None, uses the default value set in the config. Defaults to None.
            only_sql (bool, optional): If True, skips the response node and only returns the generated SQL. Defaults to False.
            **kwargs: additional keyword arguments to pass to the agent. See `SQLAgent.invoke` for arguments.
        Raises:
            ValueError: if the Chat has no id (it has not been persisted)

        Returns:
            str: last response
        """
        logfire.span(
            "New prompt submitted to chat on datasource {datasource_name}",
            datasource_name=self.datasource.name,
        )
        if self.id is None:
            raise ValueError("Chat has no id")

        final_state = self.agent.invoke(
            prompt=s,
            datasource=self.datasource,
            thread_id=self.id,
            debug=debug,
            only_sql=only_sql,
            **kwargs,
        )

        logfire.info("Response from chat")
        resp = Response(
            chat=self,
            id=len(self.responses),
            message=final_state["messages"][-1],
            text=final_state["messages"][-1].content,
            sql=final_state["sql_generation"].sql
            if final_state.get("sql_generation", None) is not None
            else None,
            sql_result=final_state.get("query_results", None),
        )

        self._responses.append(resp)
        return resp
