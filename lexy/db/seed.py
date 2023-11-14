from sqlmodel.ext.asyncio.session import AsyncSession

from lexy.db.sample_data import sample_data
from lexy.models.binding import Binding
from lexy.models.collection import Collection
from lexy.models.document import Document
from lexy.models.index import Index
from lexy.models.transformer import Transformer


async def add_sample_data_to_db(session: AsyncSession):
    session.add(Collection(**sample_data["default_collection"]))
    session.add(Collection(**sample_data["code_collection"]))
    await session.commit()
    session.add(Document(**sample_data["document_1"]))
    session.add(Document(**sample_data["document_2"]))
    session.add(Document(**sample_data["document_3"]))
    session.add(Document(**sample_data["document_4"]))
    session.add(Document(**sample_data["document_5"]))
    await session.commit()
    session.add(Transformer(**sample_data["transformer_1"]))
    session.add(Transformer(**sample_data["transformer_2"]))
    await session.commit()
    session.add(Index(**sample_data["index_1"]))
    await session.commit()
    session.add(Binding(**sample_data["binding_1"]))
    await session.commit()
