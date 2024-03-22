"""Module for creating and managing indexes"""

import logging
from datetime import datetime, date, time
from typing import Dict, ForwardRef, Literal, Optional, Type
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from pydantic import create_model
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DDL, event, inspect
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine, Inspector
from sqlmodel import SQLModel, Field, Session, select
from sqlmodel.main import RelationshipInfo

from lexy.models.index import Index
from lexy.models.index_record import IndexRecordBaseTable


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

LEXY_INDEX_FIELD_TYPES: Dict = {
    'int': int,
    'integer': int,
    'float': float,

    'str': str,
    'string': str,
    'text': str,
    'bytes': bytes,
    'bytearray': bytearray,

    'date': date,
    'datetime': datetime,
    'time': time,

    'uuid': UUID,
    'uuid1': uuid1,
    'uuid3': uuid3,
    'uuid4': uuid4,
    'uuid5': uuid5,

    'bool': bool,
    'boolean': bool,

    'dict': dict,
    'object': dict,
    'list': list,
    'array': list,
}


# class IndexField(SQLModel):
#     name: str
#     type: str
#     optional: bool = False
#     indexed: bool = False
#     extras: Dict[str, Any] | None = None
#
#     @validator('field_type')
#     def type_must_be_valid(self, v):
#         assert v in LEXY_INDEX_FIELD_TYPES.keys(), f'Invalid type: {v}, must be one of the following: ' \
#                                                    f'{", ".join(LEXY_INDEX_FIELD_TYPES.keys())}'
#         return v
#
#
# class EmbeddingField(IndexField):
#     dims: int = 384
#     model: str = 'text.embeddings.minilm'
#
#     @validator('field_type')
#     def type_must_be_valid(self, v):
#         assert v == 'embedding', f'Invalid type: {v}, must be "embedding"'
#         return v


# mapping from tablename to class
def map_tablename_to_class(SQLModel) -> dict:
    tbl_to_cls = {}
    for mapper in SQLModel._sa_registry.mappers:
        cls = mapper.class_
        classname = cls.__name__
        if not classname.startswith('_'):
            tblname = cls.__tablename__
            tbl_to_cls[tblname] = cls
    return tbl_to_cls


TBLNAME_TO_CLASS = map_tablename_to_class(SQLModel)


# TODO: add hnsw index type (e.g., cosine, euclidean, etc.) to DDL statement
class IndexManager(object):

    TBLNAME_TO_CLASS: dict | None = TBLNAME_TO_CLASS

    def __init__(self, engine: Engine):
        self._engine: Engine = engine
        self._db: Session | None = None
        self._inspector: Inspector | None = None

        self.index_models: dict[str, Type[IndexRecordBaseTable]] = {}
        logger.info(f"IndexManager initialized with db url '{repr(self.db.bind.engine.url)}'")

    # TODO: Make session management more robust, specifically by
    #  ensuring that distinct API requests don't use the same session
    @property
    def db(self) -> Session:
        if self._db is None:
            sync_session_local = sessionmaker(class_=Session, autocommit=False, autoflush=False, bind=self._engine)
            self._db = sync_session_local()
        return self._db

    @property
    def inspector(self) -> Inspector:
        if self._inspector is None:
            self._inspector = inspect(self.db.bind.engine)
        return self._inspector

    def get_indexes(self) -> list[Index]:
        """ Get all indexes """
        indexes = self.db.exec(select(Index)).all()
        return indexes

    def get_index(self, index_id: str) -> Index:
        """ Get an index by id

        Args:
            index_id (str): index id

        Returns:
            Index: index

        Raises:
            ValueError: if index is not found
        """
        index = self.db.exec(select(Index).where(Index.index_id == index_id)).first()
        if not index:
            raise ValueError(f"Index {index_id} not found")
        return index

    def create_index_models(self):
        logger.info("Creating index models")
        indexes = self.get_indexes()
        for index in indexes:
            if self.index_models.get(index.index_id):
                logger.warning(f"create_index_models -- Index model {index.index_id} already exists.")
            index_model = self.create_index_model(index)
            if self.table_exists(index.index_table_name):
                logger.info(f"create_index_models -- Index table {index.index_table_name} already exists.")
            else:
                logger.info(f"create_index_models -- Creating new Index table {index.index_table_name}.")
                created = self._create_index_table(index_model)
                if created:
                    logger.info(f"create_index_models -- Created new Index table {index.index_table_name}.")
                else:
                    logger.warning(f"create_index_models -- Failed to create Index table {index.index_table_name}.")

    def create_index_model(self, index: Index) -> Type[IndexRecordBaseTable]:
        index_table_name = index.index_table_name
        field_defs = self.get_field_definitions(index.index_fields)
        # add the Document relationship, i.e., the equivalent of the following field:
        #   document: "Document" = Relationship(back_populates="index_records")
        field_defs["document"] = (ForwardRef("Document"), RelationshipInfo())
        if index_table_name in self.TBLNAME_TO_CLASS.keys():
            logger.warning(f"create_index_model -- Index table {index_table_name} exists in TBLNAME_TO_CLASS.keys().")
            index_model = self.TBLNAME_TO_CLASS.get(index_table_name)
            self.index_models[index.index_id] = index_model
            return index_model
        index_model = create_model(
            index.index_table_schema.get("title", index_table_name),
            __base__=(IndexRecordBaseTable,),
            __cls_kwargs__={"table": True},
            __module__=__name__,
            **field_defs,
            **{"__tablename__": index.index_table_name,
               "__index_id__": index.index_id},
        )
        # attach event listener to create index on embedding fields
        embedding_ddl = self.get_ddl_for_embedding_fields(index.index_fields, index_table_name)
        for colname, ddl in embedding_ddl.items():
            event.listen(
                index_model.__table__,
                "after_create",
                ddl,
            )
        self.index_models[index.index_id] = index_model
        return index_model

    def get_or_create_index_model(self, index: Index) -> tuple[Type[IndexRecordBaseTable], bool]:
        """ Get or create an index model from an Index object.

        Args:
            index (Index): The index object to get or create the model for.

        Returns:
            tuple[Type[IndexRecordBaseTable], bool]: A tuple of the index model and a boolean indicating whether the
                model was created.
        """
        if index.index_id in self.index_models.keys():
            logger.debug(f"get_or_create_index_model -- Index model {index.index_id} already exists.")
            return self.index_models.get(index.index_id), False
        else:
            logger.debug(f"get_or_create_index_model -- Index model {index.index_id} does not exist "
                         f"- will try to create it")
            return self.create_index_model(index), True

    def create_index_model_and_table(self, index_id: str) -> tuple[bool, bool]:
        """ Create a new index model and its associated table.

        **This requires that the index row already exists in the database.**

        Steps involved:
            1. Get the index object from the indexes table
            2. Create (or get) the corresponding index model
            3. Create associated index table in the database

        Args:
            index_id (str): The ID of the index to create

        Returns:
            tuple[bool, bool]: A tuple of booleans indicating whether the index model and table were created
        """
        logger.info(f"Creating new index model and table for {index_id = }")

        # get the index object
        index = self.get_index(index_id)
        if index is None:
            raise ValueError(f"Index {index_id} not found")

        # create (or get) the corresponding index model
        index_model, model_created = self.get_or_create_index_model(index)
        if not model_created:
            # NOTE: This should only happen if an index with the same name was previously created, and then deleted
            #   with option `drop_table=False`. To force the recreation of the index or table, the user should recreate
            #   the index, then delete it with option drop_table=True.
            logger.warning(f"Index model {index_id} already exists. Skipping creation.")

        # create index table in the database
        table_created = self._create_index_table(index_model)
        if not table_created:
            logger.warning(f"Index table {index.index_table_name} already exists. Skipping creation.")

        return model_created, table_created

    def drop_index_table(self, index_id: str) -> bool:
        """ Drops the index table from the database and removes the index model from the index manager.

        Args:
            index_id (str): The ID of the index to drop.

        Returns:
            bool: True if the index table was dropped, False otherwise.
        """
        logger.info(f"Dropping index table for {index_id = }")

        index = self.get_index(index_id)

        # pop to remove the index model from self.index_models
        index_model = self.index_models.pop(index_id, None)
        # if the index model doesn't exist, log a warning and return
        if index_model is None:
            logger.warning(f"Index model for '{index_id}' does not exist")
            return False

        # if the table doesn't exist, log a warning and return
        if not self.table_exists(index.index_table_name):
            logger.warning(f"Index table '{index.index_table_name}' does not exist")
            return False

        logger.debug(f"about to drop table for index_model: {index_model}")
        index_model.metadata.drop_all(self.db.bind.engine, tables=[index_model.__table__])
        index_model.metadata.remove(index_model.__table__)
        # clear the inspector cache to ensure that `self.table_exists` works as expected
        self.inspector.clear_cache()
        return True

    def table_exists(self, index_table_name: str, use_cache: bool = True) -> bool:
        if use_cache is not True:
            self.inspector.clear_cache()
        return self.inspector.has_table(index_table_name)

    def _create_index_table(self, index_model: Type[IndexRecordBaseTable]) -> bool:
        """ Create index table from an Index model """
        # if the tablename is None, raise an error
        if index_model.__tablename__ is None:
            raise ValueError("Index model must have a __tablename__ attribute")
        # if the table already exists, log a warning and return
        if self.table_exists(index_model.__tablename__):
            logger.debug(f"Index table {index_model.__tablename__} already exists. Skipping creation.")
            return False
        index_model.metadata.create_all(self.db.bind.engine)
        # clear the inspector cache to ensure that `self.table_exists` works as expected
        self.inspector.clear_cache()
        return True

    @staticmethod
    def get_field_definitions(index_fields: dict) -> dict:
        """ Get field definitions from index fields

        Args:
            index_fields: dict representation of index fields

        Returns:
            dict: field definitions

        Examples:
            >>> sample_fields_as_dict = {
            >>>      "embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            >>>      "text": {"type": "string", "optional": True},
            >>> }
            >>> IndexManager.get_field_definitions(sample_fields_as_dict)

        """
        field_defs = {}
        for fk, fv in index_fields.items():
            fd_info = None

            if fv['type'] == 'embedding':
                embedding_args = fv['extras']
                fd_type = list[float]
                fd_info = Field(sa_column=Column(Vector(dim=embedding_args['dims'])))
            else:
                fd_type = LEXY_INDEX_FIELD_TYPES.get(fv['type'])
                if 'optional' in fv and fv['optional'] is True:
                    fd_type = Optional[fd_type]

                if fv['type'] in ['dict', 'object', 'list', 'array']:
                    fd_info = Field(sa_column=Column(JSONB), default=None)

            field_defs[fk] = (fd_type, fd_info)

        return field_defs

    @staticmethod
    def get_ddl_for_embedding_fields(
            index_fields: dict,
            tablename: str,
            vector_ops_type: Literal['vector_cosine_ops', 'vector_l2_ops', 'vector_ip_ops'] = 'vector_cosine_ops') \
            -> dict:
        """ Get DDL statements for index fields of type 'embedding'

        Args:
            index_fields: dict representation of index fields
            tablename: Name of index table
            vector_ops_type: Type of vector operations to use for the index. Default is 'vector_cosine_ops'.

        Returns:
            dict[str, DDL]: ddl statements

        Examples:
            >>> index_fields_as_dict = {
            >>>      "embedding": {"type": "embedding", "extras": {"dims": 384, "model": "text.embeddings.minilm"}},
            >>>      "text": {"type": "string", "optional": True},
            >>> }
            >>> IndexManager.get_ddl_for_embedding_fields(index_fields_as_dict, 'my_index_table')

        """
        embedding_ddl = {}
        for fk, fv in index_fields.items():
            if fv['type'] == 'embedding':
                colname = fk
                embedding_ddl[fk] = DDL(
                    f"CREATE INDEX IF NOT EXISTS ix_{tablename}_{colname}_hnsw "
                    f"ON {tablename} "
                    f"USING hnsw ({colname} {vector_ops_type}) "
                    f"WITH ("
                    f"  m = 16, "
                    f"  ef_construction = 64 "
                    f");"
                )
        return embedding_ddl
