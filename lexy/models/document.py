from datetime import datetime
from typing import Optional, Any
from uuid import uuid4, UUID

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel, Relationship

from lexy.models.collection import Collection
# from lexy.core.celery_tasks import save_result_to_index


class DocumentBase(SQLModel):
    title: str
    content: str
    meta: Optional[dict[Any, Any]] = Field(sa_column=Column(JSONB), default={})


class Document(DocumentBase, table=True):
    __tablename__ = "documents"
    document_id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False,
    )
    created_at: datetime = Field(
        nullable=False,
        sa_column=Column(DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: datetime = Field(
        nullable=False,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    collection_id: str = Field(default="default", foreign_key="collections.collection_id")
    collection: Collection = Relationship(back_populates="documents", sa_relationship_kwargs={'lazy': 'selectin'})
    embeddings: list["Embedding"] = Relationship(back_populates="document")

    # def apply_async_bindings(self):
    #     # initiate list of tasks
    #     tasks = []
    #     # loop through transformer bindings for this document
    #     for binding in self.collection.transformer_index_bindings:
    #         # check if binding is enabled
    #         if binding.status != 'on':
    #             print(
    #                 f"Skipping transformer index binding {binding} because it is not enabled (status: {binding.status})")
    #             continue
    #         # check if document matches binding filters
    #         if binding.filters and not all(f(self) for f in binding.filters):
    #             print(f"Skipping transformer index binding {binding} because document does not match filters")
    #             continue
    #         # import the transformer function
    #         # TODO: just import the function from celery?
    #         tfr_mod_name, tfr_func_name = binding.transformer.path.rsplit('.', 1)
    #         tfr_module = importlib.import_module(tfr_mod_name)
    #         transformer_func = getattr(tfr_module, tfr_func_name)
    #         # generate the task
    #         task = transformer_func.apply_async(
    #             args=[self.content],
    #             kwargs=binding.transformer_params,
    #             link=save_result_to_index.s(document_id=self.document_id,
    #                                         text=self.content,
    #                                         index_id=binding.index_id)
    #         )
    #         tasks.append({"task_id": task.id, "document_id": self.document_id})
    #     return tasks


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(DocumentBase):
    title: Optional[str] = None
    content: Optional[str] = None
    meta: Optional[dict[Any, Any]] = None


# class DocumentInDB(DocumentBase):
#     pass
