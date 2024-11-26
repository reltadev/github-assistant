import os
from langchain_openai import ChatOpenAI
from sqlmodel import Session, SQLModel, select, create_engine
from tabulate import tabulate
import duckdb
from .config import Configuration
import logfire
from .agents import SQLAgent
from .semantic import SemanticLayer
from .exceptions import DuplicateResourceException
from typing import Optional


# All SQLModels must be called here so that create_all is successful!
from .datasource import DataSource, DataSourceType
from .chat import Chat
# -- END SQLModels --


class Client:
    def __init__(self, config: Optional[Configuration] = None):
        if config is None:
            config = Configuration()
        self.config = config
        logfire.configure(
            send_to_logfire="if-token-present",
            token=self.config.logfire_token if self.config.logfire_token else None,
            console=logfire.ConsoleOptions(
                min_log_level="warning", show_project_link=False
            ),
        )
        logfire.info("Client initialized")

        self.engine = create_engine(
            f"duckdb:///{self.config.relta_internal_path}", echo=self.config.debug
        )

        folders = {
            k: v for k, v in self.config.model_dump().items() if k.endswith("_dir_path")
        }
        for fpath in folders:
            if not os.path.exists(folders[fpath]):
                logfire.info(f"Creating directory at {folders[fpath]}")
                os.mkdir(folders[fpath])

        # Populate ClassVar's from Configuration
        DataSource.conn = duckdb.connect(str(self.config.relta_data_path))
        Chat.agent = SQLAgent(self.config)
        SQLAgent.model = ChatOpenAI(model="gpt-4o-2024-08-06", temperature=0)
        SQLAgent.mini_model = ChatOpenAI(model="gpt-4o-mini-2024-07-18", temperature=0)

        # register any models
        SQLModel.metadata.create_all(self.engine)

        # re-attach any databases that were connected to the client
        self._attach_databases()

    def _attach_databases(self):
        """iterates to connected datasources and attaches them to the client"""
        with Session(self.engine) as session:
            datasources = session.exec(select(DataSource)).all()
            for datasource in datasources:
                datasource._config = self.config
                datasource._attach()

    def create_datasource(
        self,
        connection_uri: str,
        name: Optional[str] = None,
        dtypes: Optional[dict[str, str]] = None,
    ) -> DataSource:
        """Creates a new datasource object and connects it to Relta

        Args:
            connection_uri (str): The connection_uri for the datasource
            name (str, optional): The datasource name. If none is provided Relta will assign a name
            dtypes (dict, optional): Map of column names to datatypes, overrides a column's auto-detected type.
                The datatypes should be [DuckDB datatypes](https://duckdb.org/docs/sql/data_types/overview). *Only for CSVs*.

        Raises:
            duckdb.CatalogException: Raised if a datasource with given name already exists
            duckdb.BinderException: Raised if Relta cannot connect to the given database.

        Returns:
            DataSource: The newly created Datasource object
        """
        with Session(self.engine) as session:
            session.expire_on_commit = False

            if connection_uri.endswith(".csv"):
                type = DataSourceType.CSV
            elif connection_uri.endswith(".parquet"):
                type = DataSourceType.PARQUET
            elif connection_uri.startswith("postgres"):
                type = DataSourceType.POSTGRES
            elif connection_uri.startswith("mysql"):
                type = DataSourceType.MYSQL
            elif connection_uri.endswith(".duckdb") or connection_uri.endswith(".ddb"):
                type = DataSourceType.DUCKDB

            if name is None:
                name = DataSource._infer_name_if_none(
                    type=type, connection_uri=connection_uri
                )

            logfire.info(
                "Creating datasource {name} with type {type}", name=name, type=type
            )
            ds = session.exec(
                select(DataSource)
                .where(DataSource.name == name)
                .where(DataSource.connection_uri == connection_uri)
            ).first()

            if ds is not None:
                raise DuplicateResourceException(
                    f"Datasource with {name} and {connection_uri} exist. Consider using get_datasource or get_or_create_datasource."
                )

            datasource = DataSource(type=type, connection_uri=connection_uri, name=name)
            datasource._config = self.config

            try:
                datasource.connect(dtypes=dtypes)
            except duckdb.CatalogException:
                logfire.error("A table with the same name already exists in Relta")
                raise duckdb.CatalogException(
                    "A table with the same name already exists in Relta"
                )
            except duckdb.BinderException:
                logfire.error("A table with the same name already exists in Relta")
                raise duckdb.BinderException(
                    "A database with same name is already connected to Relta"
                )

            datasource._semantic_layer = SemanticLayer(datasource, self.config)
            session.add(datasource)
            session.commit()
            return datasource

    def get_datasource(self, name: str) -> DataSource:
        """Returns a datasource object with given name or id

        Args:
            name (str): The name of the datasource. Must be passed in.

        Returns:
            DataSource: The Datasource object or None if it does not exist
        """
        with Session(self.engine) as session:
            ds = session.exec(select(DataSource).where(DataSource.name == name)).first()
            if ds is None:
                return None
            ds._config = self.config
            ds._semantic_layer = SemanticLayer(ds, self.config)
            return ds

    def get_or_create_datasource(self, name: str, connection_uri: str) -> DataSource:
        """If a datasource with the same name and same connection_uri exist we return it. Otherwise create a new one.

        Args:
            name (str): the name of the datasource to get or create
            connection_uri (str): the connection_uri to the datasource to get or create

        Returns:
            DataSource: The existng datasource or the new one
        """
        with Session(self.engine) as session:
            ds = session.exec(
                select(DataSource)
                .where(DataSource.name == name)
                .where(DataSource.connection_uri == connection_uri)
            ).first()
            if ds is None:
                return self.create_datasource(name=name, connection_uri=connection_uri)

            ds._config = self.config
            ds._semantic_layer = SemanticLayer(ds, self.config)
            return ds

    def delete_datasource(self, name: str) -> None:
        """Deletes DataSource and all associated Chat objects from Relta. Cannot be reversed.

        Args:
            name: the datasource name

        Raises:
            ValueError: If DataSource does not exist
        """

        datasource = self.get_datasource(name)
        if datasource is None:
            raise ValueError("Datasource does not exist")

        datasource._disconnect()

        # we have to delete Chats and split into two commits because of a limitation of duckdb indexes.
        with Session(self.engine) as session:
            session.expire_on_commit = False
            chats = session.exec(
                select(Chat).where(Chat.datasource_id == datasource.id)
            ).all()
            for chat in chats:
                session.delete(chat)
            session.commit()

        with Session(self.engine) as session:
            session.delete(datasource)
            session.commit()

    def get_sources(self) -> list[DataSource]:
        """Method to get all connected datasource objects

        Returns:
            list[DataSource]: A list containing DataSource objects for all connected sources
        """
        with Session(self.engine) as session:
            ds_lst = session.exec(select(DataSource)).all()
            for ds in ds_lst:
                ds._config = self.config
                ds._semantic_layer = SemanticLayer(ds, self.config)
            return ds_lst

    def show_sources(self) -> None:
        """Prints a table of all connected datasources to the console"""
        with Session(self.engine) as session:
            datasources = session.exec(select(DataSource)).all()
            datasources_dicts = [
                dict(sorted(datasource.model_dump().items()))
                for datasource in datasources
            ]
            headers = sorted(DataSource.model_fields())
            rows = [datasource.values() for datasource in datasources_dicts]

            print(tabulate(rows, headers=headers, tablefmt="pretty"))

    def create_chat(self, datasource: DataSource) -> Chat:
        """Creates a chat with the given DataSource"""
        logfire.info("New chat created with datasource {name}", name=datasource.name)
        chat = Chat(datasource_id=datasource.id, datasource=datasource)
        chat._config = self.config
        chat._responses = []
        with Session(self.engine) as session:
            session.expire_on_commit = False
            session.add(chat)
            session.commit()
        return chat

    def list_chats(self, datasource: DataSource) -> list[Chat]:
        """List all Chat objects for a given DataSource"""
        with Session(self.engine) as session:
            chats = session.exec(
                select(Chat).where(Chat.datasource_id == datasource.id)
            ).all()

            for chat in chats:
                chat._config = self.config
                chat._responses = []
                chat.datasource = datasource

            return chats

    def get_chat(self, datasource: DataSource, id: int) -> Chat:
        with Session(self.engine) as session:
            chat = session.exec(
                select(Chat)
                .where(Chat.id == id)
                .where(Chat.datasource_id == datasource.id)
            ).first()
            if chat is None:
                raise NameError(
                    f"Chat '{id}' does not exist on DataSource {datasource.name}"
                )
            chat._config = self.config
            chat._responses = []  # TODO: make responses load in when getting a chat again
            chat.datasource = datasource
            return chat
