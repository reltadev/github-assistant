from abc import ABC, abstractmethod
from typing import ClassVar, final
from sqlmodel import MetaData


class SchemaMixin(ABC):
    """Mixin class used to define a non-default schema in storage.

    The children mixins should be inherited by `SQLModel` classes to enforce the schema that `SQLModel` is in.
    """

    @property
    @abstractmethod
    def metadata(self) -> MetaData:
        pass

    @classmethod
    def get_schema_name(cls):
        return cls.metadata.schema


@final
class ReltaInternalSchemaMixin(SchemaMixin):
    """Mixin for internal schema (`relta_internal`)."""

    metadata: ClassVar[MetaData] = MetaData(schema="relta_internal")


# currently unused, but could be useful in the future
def get_subclasses(cls: object) -> set[object]:
    """Recursively get all subclasses of a class.

    Args:
        cls (object): root class

    Returns:
        All subclasses in recursive search.
    """
    subclasses = set()
    for subcl in cls.__subclasses__():
        subclasses.add(subcl)
        subclasses.update(get_subclasses(subcl))
    return subclasses
