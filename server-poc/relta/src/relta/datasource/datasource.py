from enum import Enum
import duckdb
from sqlmodel import Field, SQLModel, Relationship, Sequence
from urllib.parse import urlparse
from datetime import datetime
from typing import ClassVar, Optional
import logging
from sqlglot import parse_one, exp
from ..semantic import SemanticLayer
from ..config import Configuration
import logfire
import os
from deprecated import deprecated
import re


logger = logging.getLogger("datasource")


class DataSourceType(Enum):
    CSV = 1
    PARQUET = 2
    POSTGRES = 3
    MYSQL = 4
    DUCKDB = 5


source_id_seq = Sequence("source_id_seq", metadata=SQLModel.metadata)


class DataSource(SQLModel, table=True):
    conn: ClassVar[
        duckdb.DuckDBPyConnection
    ]  # populated when a Client is initialized. ClassVar is not serialized by SQLModel
    # this connection is for the external data source, not for accessing the Relta replica.

    id: Optional[int] = Field(default=source_id_seq.next_value(), primary_key=True)
    type: DataSourceType
    connection_uri: str
    name: str
    last_hydrated: Optional[datetime] = Field(default=None)

    # These private fields are populated on creation or load.
    # They aren't validated by SQLModel (even if you pass them in on __init__ as private attributes, no matter the ConfigDict(extra="allow"))
    _config: Configuration
    _semantic_layer: SemanticLayer

    chats: list["Chat"] = Relationship(back_populates="datasource")  # type: ignore # noqa: F821 # avoid circular import w quotes

    @property
    def semantic_layer(self):
        """The semantic layer of the `DataSource`. Populated by `Client`"""
        return self._semantic_layer

    def _attach(self):
        """Attaches the database to Relta. This is called at client initialization.

        Raises:
            NotImplementedError: If the data source type is not supported
        """
        if self.type == DataSourceType.POSTGRES:
            self.conn.sql("INSTALL POSTGRES")
            self._connect_postgres()
        elif self.type == DataSourceType.MYSQL:
            self._connect_mysql()
        elif self.type == DataSourceType.CSV:
            self._connect_csv()
        elif self.type == DataSourceType.DUCKDB:
            self._connect_duckdb()
        else:
            raise NotImplementedError

    def _connect_duckdb(self):
        """Private method used to connect to a DuckDB datasource"""
        try:
            self.conn.sql(f"ATTACH '{self.connection_uri}' AS {self.name}")

            self.conn.sql(
                f"ATTACH '{self._config.transient_data_dir_path}/{self.name}.duckdb' AS transient_{self.name}"
            )

        except duckdb.BinderException as e:
            logfire.error(e)
            logfire.error(
                f"Unable to attach to DuckDB database with connection URI {self.connection_uri}. This could be because the connection_uri is wrong or database with same name already exists in Relta."
            )
            raise duckdb.BinderException

    def _connect_postgres(self):
        """Private method used to connect to a Postgres data source"""
        parsed_uri = urlparse(self.connection_uri)
        try:
            self.conn.sql(
                f"ATTACH 'dbname={parsed_uri.path.lstrip('/')} {f'host={parsed_uri.hostname}' if parsed_uri.hostname else ''} {f'user={parsed_uri.username}' if parsed_uri.username else ''} {f'password={parsed_uri.password}' if parsed_uri.password else ''} {f'port={parsed_uri.port}' if parsed_uri.port else ''}' AS {self.name} (TYPE POSTGRES, READ_ONLY)"
            )

            self.conn.sql(
                f"ATTACH '{self._config.transient_data_dir_path}/{self.name}.duckdb' AS transient_{self.name}"
            )
        except duckdb.BinderException as e:
            logfire.error(e)
            logfire.error(
                f"Unable to attach to Postgres database with connection URI {self.connection_uri}. This could be because the connection_uri is wrong or database with same name already exists in Relta."
            )
            raise duckdb.BinderException

    def _connect_mysql(self):
        raise NotImplementedError

    def _connect_csv(self, dtypes: Optional[dict[str, str]] = None):
        """Private method used to connect to a CSV data source and create a table in Relta

        Args:
            dtypes (dict, optional): Map of column names to datatypes, overrides a column's auto-detected type.
                The datatypes should be [DuckDB datatypes](https://duckdb.org/docs/sql/data_types/overview).

        Raises:
            duckdb.CatalogException: raised if a table with the same name already exists in Relta
        """
        try:
            self.conn.sql(
                f"ATTACH '{self._config.transient_data_dir_path}/{self.name}.duckdb' AS transient_{self.name}"
            )
            self._load_csv(dtypes)
        except duckdb.CatalogException as e:
            logfire.error(e)
            logfire.error(
                f"Table with name {self.name} already exists in Relta. Please choose a different name or consider refreshing data using rehydrate()"
            )
            raise duckdb.CatalogException

    def _connect_parquet(self):
        raise NotImplementedError

    def connect(self, dtypes: Optional[dict[str, str]] = None):
        """Creates a connection to the given data source. This allows Relta to query the underlying data (e.g. read schema) but does not copy data into Relta.

        Args:
            dtypes (dict, optional): Map of column names to datatypes, overrides a column's auto-detected type.
                *Only for CSVs*. The datatypes should be [DuckDB datatypes](https://duckdb.org/docs/sql/data_types/overview).

        Raises:
            duckdb.CatalogException: If a table with the same name is already connected to Relta
        """
        if self.type == DataSourceType.CSV:
            self._connect_csv(dtypes)
        elif self.type == DataSourceType.PARQUET:
            self._connect_parquet()
        elif self.type == DataSourceType.POSTGRES:
            self._connect_postgres()
        elif self.type == DataSourceType.MYSQL:
            self._connect_mysql()
        elif self.type == DataSourceType.DUCKDB:
            self._connect_duckdb()

    def _disconnect(self):
        """Disconnects the data source from Relta

        Raises:
            duckdb.CatalogException: If the underlying data source does not exist in Relta
        """
        self.conn.sql(
            "ATTACH IF NOT EXISTS ':memory:' AS memory_db"
        )  # this is to gaurd in case the DB we are deleting is the default database
        try:
            if (
                self.type == DataSourceType.POSTGRES
                or self.type == DataSourceType.DUCKDB
            ):
                self.conn.sql("USE memory_db")
                self.conn.sql(f"DETACH {self.name}")
                os.remove(f"{self._config.transient_data_dir_path}/{self.name}.duckdb")
            elif self.type == DataSourceType.CSV:
                self.conn.sql("USE memory_db")
                self.conn.sql(f"DETACH  transient_{self.name}")
                os.remove(f"{self._config.transient_data_dir_path}/{self.name}.duckdb")

        except duckdb.CatalogException as e:
            logfire.error(e)
            logfire.error(
                f"Table with name {self.name} does not exist in Relta. Please check the name and try again"
            )
            raise duckdb.CatalogException

    def load(self):
        """Updates the data in Relta from the underlying data source"""
        if self.type == DataSourceType.POSTGRES:
            self._load_postgres()
        elif self.type == DataSource.DUCKDB:
            self._load_postgres()
        elif self.type == DataSourceType.CSV:
            self._load_csv()

    def _load_csv(self, dtypes: Optional[dict[str, str]] = None):
        self.last_hydrated = datetime.now()
        self.conn.sql(f"USE transient_{self.name}")
        if dtypes:
            create_table_sql = f"CREATE OR REPLACE TABLE {self.name} AS SELECT * from read_csv('{self.connection_uri}', types = {dtypes})"
        else:
            create_table_sql = f"CREATE OR REPLACE TABLE {self.name} AS SELECT * from read_csv('{self.connection_uri}')"

        self.conn.sql(create_table_sql)
        self.last_hydrated = datetime.now()

    def _load_postgres(self):
        self.conn.sql("USE relta_data")
        self.conn.sql(
            f"ATTACH IF NOT EXISTS '{self._config.transient_data_dir_path}/transient_{self.name}.duckdb' As transient_{self.name}"
        )

        self.conn.sql(f"USE transient_{self.name}")
        for metric in self._semantic_layer.metrics:
            self.conn.sql(
                f"CREATE TABLE IF NOT EXISTS {metric.name} AS {metric.sql_to_underlying_datasource}"
            )
            # for column in metric.dimensions:
            #    self.conn.sql(f"CREATE OR REPLACE VIEW {metric.name} AS SELECT {column}, {metric.name} FROM {self.name}")

        self.last_hydrated = datetime.now()  # TODO: this needs to be written to the database, but that is a client operation... what to do about this?
        # TODO: when to detach? it should be after hydrating?

    @deprecated(reason="Use DataSource().semantic_layer property instead")
    def create_semantic_layer(self) -> SemanticLayer:
        """Returns the semantic model of the data source"""
        self._semantic_layer = SemanticLayer(self, self._config)
        return self._semantic_layer

    @deprecated(reason="Use DataSource().semantic_layer property instead")
    def get_semantic_layer(self) -> SemanticLayer:
        return self._semantic_layer

    def _get_ddl(self) -> str:
        """Returns the DDL of the data source"""

        if self.type == DataSourceType.POSTGRES or self.type == DataSourceType.DUCKDB:
            ddl_list = self.conn.sql(
                f"select sql from duckdb_tables() where database_name='{self.name}' and schema_name != 'information_schema' and schema_name != 'pg_catalog'"
            ).fetchall()
            ddl = "\n".join([ddl[0] for ddl in ddl_list])
        elif self.type == DataSourceType.CSV:
            ddl = self.conn.sql(
                f"select sql from duckdb_tables() where table_name='{self.name}'"
            ).fetchone()[0]  # self.conn.sql(f"DESCRIBE {self.name}")

        return ddl

    def _create_metrics(self):
        self.conn.sql("USE relta_data")
        for metric in self._semantic_layer.metrics:
            # fully_formed_sql = self._append_db_to_table_name(metric.sql_to_underlying_datasource, f'transient_{self.name}')
            self.conn.sql(
                f"CREATE OR REPLACE VIEW {metric.name} AS select * from transient_{self.name}.{metric.name}"
            )

    def _execute_datasource_sql(self, sql: str):
        """Run SQL against the underlying datasource"""
        if self.type == DataSourceType.CSV:
            self.conn.sql(f"USE transient_{self.name}")
            return self.conn.sql(sql)
        else:
            raise NotImplementedError

    def _execute_sql(self, sql: str):
        self.conn.sql("USE relta_data")
        return self.conn.sql(sql)

    def _get_transient_ddl(self):
        # self.conn.sql(f"USE transient_{self.name}")
        return self.conn.sql(
            f"SELECT * FROM duckdb_tables() where database_name='transient_{self.name}'"
        ).fetchall()

    @staticmethod
    def _append_db_to_table_name(original_sql: str, db_name: str) -> str:
        """In DuckDB we need fully formed table and column names with database name appended. This method creates those.

        Args:
            original_sql (str): the sql we will be modifying

        Returns:
            str: The SQL statement with db name appended to table names
        """
        fully_formed_sql = original_sql
        table_names = list(parse_one(fully_formed_sql).find_all(exp.Table))
        tables = [
            str(table).partition(" ")[0] for table in table_names
        ]  # this is bc sqlglot returns the table name as '{TABLE NAME} AS {ALIAS}'
        tables = set(tables)
        for table in tables:
            fully_formed_sql = re.sub(
                r"\b" + re.escape(table) + r"\b",
                f"{db_name}.{table}",
                fully_formed_sql,
            )

        return fully_formed_sql

    def _create_transient_tables(self, calculate_statistics: bool = True):
        """Creates the transient tables in DuckDB

        Args:
            calculate_statistics (bool, optional): Calculate statistics (i.e. low cardinality columns) for each metric. Defaults to True.
        """
        self.conn.sql(f"USE transient_{self.name}")

        if self.type == DataSourceType.POSTGRES or self.type == self.type.DUCKDB:
            for metric in self._semantic_layer.metrics:
                fully_formed_sql_to_underlying_source = self._append_db_to_table_name(
                    metric.sql_to_underlying_datasource, self.name
                )
                self.conn.sql(
                    f"CREATE OR REPLACE TABLE {metric.name} AS {fully_formed_sql_to_underlying_source}"
                )

        elif self.type == DataSourceType.CSV:
            for metric in self._semantic_layer.metrics:
                fully_formed_sql_to_underlying_source = self._append_db_to_table_name(
                    metric.sql_to_underlying_datasource, f"transient_{self.name}"
                )
                self.conn.sql(
                    f"CREATE OR REPLACE TABLE {metric.name} AS {fully_formed_sql_to_underlying_source}"
                )

        if calculate_statistics:
            # the following code identifies low cardinality columns
            for metric in self.semantic_layer.metrics:
                for dimension in metric.dimensions:
                    dimension.categories = []
                    cardinality = self.conn.sql(
                        f"SELECT approx_count_distinct({dimension.name}) from {metric.name}"
                    ).fetchone()[0]
                    if cardinality < 100:
                        categories = [
                            value[0]
                            for value in self.conn.sql(
                                f"SELECT DISTINCT {dimension.name} FROM {metric.name}"
                            ).fetchall()
                        ]
                        dimension.categories = categories

    def deploy(self, statistics: bool = True):
        """
        Deploys the semantic layer to the data source.

        Args:
            statistics (bool, optional): Calculate statistics (i.e. low cardinality columns) for each metric. Defaults to True.
        """
        logfire.span(
            "deploying semantic layer {semantic_layer}",
            semantic_layer=self.semantic_layer,
        )
        self._drop_removed_metrics()
        self._create_transient_tables(statistics)
        self._create_metrics()
        logfire.info("semantic layer deployed")

    def _drop_removed_metrics(self):
        """Checks the current list of metrics against views and transient tables. Drop them if they are no longer in the semantic layer"""
        self.conn.sql("use relta_data")
        if self.type == DataSourceType.CSV:  # on CSV we copy the entire data as a table
            existing_metrics = self.conn.sql(
                f"SELECT table_name FROM duckdb_tables() where database_name='transient_{self.name}' and table_name!='{self.name}'"
            ).fetchall()
        else:
            existing_metrics = self.conn.sql(
                f"SELECT table_name FROM duckdb_tables() where database_name='transient_{self.name}'"
            ).fetchall()

        existing_metric_names = [metric[0] for metric in existing_metrics]
        metric_names_to_keep = [metric.name for metric in self._semantic_layer.metrics]

        for metric_name in existing_metric_names:
            if metric_name not in metric_names_to_keep:
                self.conn.sql(
                    f"DROP TABLE IF EXISTS transient_{self.name}.{metric_name}"
                )
                self.conn.sql(f"DROP VIEW IF EXISTS {metric_name}")

    @staticmethod
    def _infer_name_if_none(type: DataSourceType, connection_uri: str) -> str:
        if type is DataSourceType.CSV or type is DataSourceType.DUCKDB:
            name = (
                connection_uri.split("/")[-1]
                .split(".")[0]
                .replace(" ", "_")
                .replace("-", "_")
            )
        elif type is DataSourceType.POSTGRES or DataSourceType.DUCKDB:
            name = connection_uri.split("/")[-1]

        return name
