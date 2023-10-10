"""Module for creating and managing indexes"""

import logging
from datetime import datetime, date, time
from typing import Dict, Optional
from uuid import UUID, uuid1, uuid3, uuid4, uuid5

from pydantic import create_model
from sqlalchemy import Column, DDL, event, inspect, REAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import sessionmaker
from sqlmodel import ARRAY, SQLModel, Field

from lexy.db.session import sync_engine
from lexy.models.binding import TransformerIndexBinding
from lexy.models.index import Index
from lexy.models.index_record import IndexRecordBaseTable


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
insp = inspect(sync_engine)

LEXY_INDEX_FIELD_TYPES: Dict = {
    'int': int,
    'integer': int,
    'float': float,

    'str': str,
    'string': str,
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
#     distance: str = 'cos'
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

    _db = None
    index_models = {}
    TBLNAME_TO_CLASS = TBLNAME_TO_CLASS

    @property
    def db(self):
        if self._db is None:
            self._db = SyncSessionLocal()
        return self._db

    def get_indexes(self) -> list[Index]:
        """ Get all indexes """
        indexes = self.db.query(Index).all()
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
        index = self.db.query(Index).filter(Index.index_id == index_id).first()
        if not index:
            raise ValueError(f"Index {index_id} not found")
        return index

    def create_index_models(self):
        logger.info("Creating index models")
        indexes = self.get_indexes()
        for index in indexes:
            if self.table_exists(index.index_table_name):
                logger.warning(f"Index table {index.index_table_name} already exists.")
            self.create_index_model(index)

    def create_index_model(self, index: Index):
        index_table_name = index.index_table_name
        field_defs = self.get_field_definitions(index.index_fields)
        if index_table_name in self.TBLNAME_TO_CLASS.keys():
            logger.warning(f"Index table {index_table_name} already exists.")
            index_model = self.TBLNAME_TO_CLASS.get(index_table_name)
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

    @staticmethod
    def get_field_definitions(index_fields: dict) -> dict:
        """ Get field definitions from index fields

        Args:
            index_fields: dict representation of index fields

        Returns:
            dict: field definitions

        Examples:
            >>> sample_fields_as_dict = {
            >>>      "embedding": {"type": "embedding", "extras": {"dims": 384, "distance": "cos"}},
            >>>      "text": {"type": "string", "optional": True},
            >>> }
            >>> IndexManager.get_field_definitions(sample_fields_as_dict)

        """
        field_defs = {}
        for fk, fv in index_fields.items():
            fd_info = None

            if fv['type'] == 'embedding':
                fd_type = list[float]
                fd_info = Field(sa_column=Column(ARRAY(REAL)))
            else:
                fd_type = LEXY_INDEX_FIELD_TYPES.get(fv['type'])
                if 'optional' in fv and fv['optional'] is True:
                    fd_type = Optional[fd_type]

                if fv['type'] in ['dict', 'object', 'list', 'array']:
                    fd_info = Field(sa_column=Column(JSONB), default=None)

            field_defs[fk] = (fd_type, fd_info)

        return field_defs

    @staticmethod
    def get_ddl_for_embedding_fields(index_fields: dict, tablename) -> dict:
        """ Get DDL statements for index fields of type 'embedding'

        Args:
            index_fields: dict representation of index fields
            tablename: name of index table

        Returns:
            dict[str, DDL]: ddl statements

        Examples:
            >>> index_fields_as_dict = {
            >>>      "embedding": {"type": "embedding", "extras": {"dims": 384, "distance": "cos"}},
            >>>      "text": {"type": "string", "optional": True},
            >>> }
            >>> IndexManager.get_ddl_for_embedding_fields(index_fields_as_dict, 'my_index_table')

        """
        embedding_ddl = {}
        for fk, fv in index_fields.items():
            if fv['type'] == 'embedding':
                colname = fk
                embedding_args = fv['extras']
                embedding_ddl[fk] = DDL(
                    f"CREATE INDEX IF NOT EXISTS ix_{tablename}_{colname}_hnsw "
                    f"ON {tablename} "
                    f"USING hnsw ({colname}) "
                    f"WITH ("
                    f"  dims = {embedding_args['dims']}, "
                    f"  m = 8, "
                    f"  efconstruction = 16, "
                    f"  efsearch = 16"
                    f");"
                )
        return embedding_ddl

    # TODO: this should probably live outside the index manager
    def switch_binding_status(self, binding: TransformerIndexBinding, status: str) -> TransformerIndexBinding:
        """ Switch binding status """
        prev_status = binding.status
        logger.debug(f"Switching status for binding {binding}: from '{prev_status}' to '{status}'")
        binding.status = status
        self.db.add(binding)
        self.db.commit()
        self.db.refresh(binding)
        logger.info(f"Switched status for binding {binding}: from '{prev_status}' to '{status}'")
        return binding

    @staticmethod
    def table_exists(index_table_name: str) -> bool:
        return insp.has_table(index_table_name)


index_manager = IndexManager()
index_manager.create_index_models()

