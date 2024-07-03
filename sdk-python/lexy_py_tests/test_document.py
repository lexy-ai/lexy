from datetime import datetime
from io import BytesIO

import asyncio
import httpx
import pytest
from PIL import Image

from lexy_py.exceptions import LexyAPIError
from lexy_py.document.models import Document
from lexy_py.storage import presigned_url_is_expired


class TestDocumentClient:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    def test_documents(self, lx_client):
        # create a test collection for test documents
        tmp_collection = lx_client.create_collection(
            "test_documents", description="Temp collection"
        )
        assert tmp_collection.collection_name == "test_documents"
        tmp_collection_id = tmp_collection.collection_id

        # add documents to the test collection
        docs_added = lx_client.add_documents(
            docs=[
                {"content": "Test Document 1 Content"},
                {
                    "content": "Test Document 2 Content",
                    "meta": {"my_date": datetime.now()},
                },
            ],
            collection_name="test_documents",
        )
        assert len(docs_added) == 2
        assert docs_added[0].content == "Test Document 1 Content"
        assert docs_added[1].content == "Test Document 2 Content"
        assert docs_added[0].document_id is not None
        assert docs_added[0].created_at is not None
        assert docs_added[0].image is None
        assert docs_added[0].collection_id == tmp_collection_id

        # get test document
        test_document = lx_client.get_document(docs_added[0].document_id)
        assert test_document.document_id == docs_added[0].document_id
        assert test_document.content == "Test Document 1 Content"

        # update test document
        doc_updated = lx_client.update_document(
            document_id=test_document.document_id,
            content="Test Document 1 Updated Content",
        )
        updated_document = lx_client.get_document(doc_updated.document_id)
        assert updated_document.document_id == test_document.document_id
        assert updated_document.content == "Test Document 1 Updated Content"
        assert updated_document.updated_at > updated_document.created_at

        # delete test document
        response = lx_client.delete_document(document_id=updated_document.document_id)
        assert response.get("msg") == "Document deleted"
        assert response.get("document_id") == updated_document.document_id

        # delete remaining test documents
        response = lx_client.delete_document(document_id=docs_added[1].document_id)
        assert response.get("msg") == "Document deleted"
        assert response.get("document_id") == docs_added[1].document_id

        # verify that there are no documents in the test collection
        documents = lx_client.list_documents(collection_name="test_documents")
        assert len(documents) == 0

        # delete test collection
        response = lx_client.delete_collection(collection_name="test_documents")
        assert response == {
            "msg": "Collection deleted",
            "collection_id": tmp_collection_id,
            "documents_deleted": 0,
        }

    def test_duplicate_documents(self, lx_client):
        # create a test collection for testing duplicate documents
        tmp_collection = lx_client.create_collection(
            "test_duplicate_documents", description="Temp collection"
        )
        assert tmp_collection.collection_name == "test_duplicate_documents"
        tmp_collection_id = tmp_collection.collection_id

        # add documents to the test collection
        docs_added = lx_client.add_documents(
            docs=[{"content": "What's up doc?"}],
            collection_name="test_duplicate_documents",
        )
        assert len(docs_added) == 1
        doc_added = docs_added[0]
        assert doc_added.document_id is not None

        # add duplicate document
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.add_documents([doc_added])
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]["msg"]
            == f"A document with this ID already exists: {doc_added.document_id}."
        )
        assert (
            exc_info.value.response.json()["detail"]["document_id"]
            == doc_added.document_id
        )

        # delete test documents
        response = lx_client.document.bulk_delete_documents(
            collection_name="test_duplicate_documents"
        )
        assert response == {
            "msg": "Documents deleted",
            "collection_id": tmp_collection_id,
            "deleted_count": 1,
        }

        # delete test collection
        response = lx_client.collection.delete_collection(
            collection_name="test_duplicate_documents"
        )
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == tmp_collection_id

    def test_add_documents_in_batches(self, lx_client):
        # create a test collection for testing adding documents in batches
        tmp_collection = lx_client.create_collection(
            "test_add_documents_in_batches", description="Temp collection"
        )
        assert tmp_collection.collection_name == "test_add_documents_in_batches"
        tmp_collection_id = tmp_collection.collection_id

        # add documents to the test collection
        docs_added = lx_client.add_documents(
            docs=[
                {"content": "Test Document 1 Content"},
                {"content": "Test Document 2 Content"},
                {"content": "Test Document 3 Content"},
            ],
            collection_name="test_add_documents_in_batches",
            batch_size=2,
        )
        assert len(docs_added) == 3
        assert docs_added[-1].document_id is not None
        assert docs_added[-1].content == "Test Document 3 Content"

        # delete test documents
        response = lx_client.document.bulk_delete_documents(
            collection_name="test_add_documents_in_batches"
        )
        assert response.get("msg") == "Documents deleted"
        assert response.get("deleted_count") == 3

        # delete test collection
        response = lx_client.delete_collection(
            collection_name="test_add_documents_in_batches"
        )
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == tmp_collection_id

    @pytest.mark.asyncio
    async def test_add_documents(self, lx_client, celery_app, celery_worker):
        default_collection = lx_client.get_collection(collection_name="default")
        doc_added = lx_client.add_documents([{"content": "hello from lexy_py!"}])
        print(f"{doc_added = }")
        assert len(doc_added) == 1
        assert doc_added[0].content == "hello from lexy_py!"
        assert doc_added[0].document_id is not None
        assert doc_added[0].created_at is not None
        assert doc_added[0].updated_at is not None
        assert doc_added[0].collection_id == default_collection.collection_id
        assert doc_added[0].image is None

        # wait for the celery worker to finish the task
        await asyncio.sleep(2)

        index_records = lx_client.index.list_index_records(
            index_id="default_text_embeddings", document_id=doc_added[0].document_id
        )
        assert len(index_records) == 1

    @pytest.mark.asyncio
    async def test_aadd_documents(self, lx_async_client, celery_app, celery_worker):
        default_collection = await lx_async_client.collection.aget_collection(
            collection_name="default"
        )
        doc_added = await lx_async_client.document.aadd_documents(
            [{"content": "an async hello from lexy_py!"}]
        )
        print(f"{doc_added = }")
        assert len(doc_added) == 1
        assert doc_added[0].content == "an async hello from lexy_py!"
        assert doc_added[0].document_id is not None
        assert doc_added[0].created_at is not None
        assert doc_added[0].updated_at is not None
        assert doc_added[0].collection_id == default_collection.collection_id
        # FIXME: Uncomment the following line after fixing the simultaneous clients
        #   issue. The issue is caused by the following line when trying to access the
        #   image property:
        #      r = self.client.get(f"/documents/{document_id}/urls",
        #                          params={"expiration": expiration})
        #   Need to figure out how to substitute get_document_urls with
        #   aget_document_urls.
        # assert doc_added[0].image is None

        # wait for the celery worker to finish the task
        await asyncio.sleep(2)

        index_records = await lx_async_client.index.alist_index_records(
            index_id="default_text_embeddings", document_id=doc_added[0].document_id
        )
        assert len(index_records) == 1

    def test_list_documents(self, lx_client):
        documents = lx_client.document.list_documents(collection_name="default")
        assert len(documents) > 0

    @pytest.mark.asyncio
    async def test_alist_documents(self, lx_async_client):
        documents = await lx_async_client.document.alist_documents(
            collection_name="default"
        )
        assert len(documents) > 0

    def test_list_documents_without_collection_name_or_id(self, lx_client):
        with pytest.raises(LexyAPIError) as exc_info:
            lx_client.document.list_documents(collection_name=None, collection_id=None)
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response.status_code == 404
        assert exc_info.value.response.json()["detail"] == "Collection not found"

    @pytest.mark.asyncio
    async def test_upload_documents(self, lx_client, settings, document_storage):
        # create a test collection for testing uploading documents
        tmp_collection = lx_client.create_collection(
            collection_name="test_upload_documents", description="Test Upload Documents"
        )
        assert tmp_collection.collection_name == "test_upload_documents"
        assert tmp_collection.description == "Test Upload Documents"
        assert tmp_collection.config == settings.COLLECTION_DEFAULT_CONFIG
        tmp_collection_id = tmp_collection.collection_id
        storage_bucket = tmp_collection.config.get("storage_bucket")
        assert storage_bucket == settings.DEFAULT_STORAGE_BUCKET

        # upload documents to the test collection
        # NOTE: file paths are relative to the execution directory (i.e., project root)
        docs_uploaded = lx_client.upload_documents(
            files=[
                "sample_data/images/lexy-dalle.jpeg",
                "sample_data/images/lexy.png",
            ],
            collection_name="test_upload_documents",
        )
        assert len(docs_uploaded) == 2
        assert docs_uploaded[0].content == "<Image(lexy-dalle.jpeg)>"
        assert docs_uploaded[1].content == "<Image(lexy.png)>"

        img_doc = docs_uploaded[0]
        assert img_doc.content == "<Image(lexy-dalle.jpeg)>"
        assert img_doc.document_id is not None
        assert img_doc.created_at is not None
        assert img_doc.updated_at is not None
        assert img_doc.collection_id == tmp_collection_id
        assert img_doc.object_url is not None
        assert img_doc.client is not None
        assert img_doc.client == lx_client

        # Setting the client to None allows loading the image through httpx, but breaks
        # the `.client` property
        # img_doc._client = None
        # assert img_doc.image is not None

        print(f"{img_doc.object_url = }")

        # FIXME: lx_client.get() returns a 404 but httpx.get() returns a 200 - this is
        #  because we're appending the API_PREFIX (e.g., "/api") to the base_url
        r = img_doc.client.get(img_doc.object_url, follow_redirects=True)
        print(f"{r.status_code = }")

        r2 = lx_client.get(img_doc.object_url, follow_redirects=True)
        print(f"{r2.status_code = }")

        r3 = httpx.get(img_doc.object_url, follow_redirects=True)
        print(f"{r3.status_code = }")

        # assert isinstance(img_doc.image, Image.Image)
        img = Image.open(BytesIO(r3.content))
        assert isinstance(img, Image.Image)
        assert img_doc.meta["filename"] == "lexy-dalle.jpeg"
        assert img_doc.meta["storage_bucket"] == storage_bucket
        assert (
            img_doc.meta["storage_key"]
            == f"lexy_tests/collections/{tmp_collection_id}/documents/lexy-dalle.jpeg"
        )
        assert img_doc.meta["size"] == 113352
        assert img_doc.meta["type"] == "image"
        assert img_doc.meta["content_type"] == "image/jpeg"
        assert img_doc.meta["image"]["width"] == 1024
        assert img_doc.meta["image"]["height"] == 1024
        assert "thumbnails" in img_doc.meta["image"]
        thumbnail_dims = list(settings.IMAGE_THUMBNAIL_SIZES)[0]
        thumbnail_dims_str = f"{thumbnail_dims[0]}x{thumbnail_dims[1]}"
        assert thumbnail_dims_str in img_doc.meta["image"]["thumbnails"]
        assert (
            img_doc.meta["image"]["thumbnails"][thumbnail_dims_str]["storage_bucket"]
            == storage_bucket
        )
        assert img_doc.meta["image"]["thumbnails"][thumbnail_dims_str][
            "storage_key"
        ] == (
            f"lexy_tests/collections/{tmp_collection_id}/thumbnails/"
            f"{thumbnail_dims_str}/lexy-dalle.jpeg"
        )

        # upload more image documents in batches
        # NOTE: file paths are relative to the execution directory (i.e., project root)
        more_img_docs = tmp_collection.upload_documents(
            files=[
                "sample_data/images/lexy-dalle.jpeg",
                "sample_data/images/lexy.png",
                "sample_data/images/lexy-dalle.jpeg",
            ],
            filenames=["junk1.jpeg", "junk2.jpeg", "junk3.jpeg"],
            batch_size=2,
        )
        assert len(more_img_docs) == 3
        assert more_img_docs[0].content == "<Image(junk1.jpeg)>"
        assert more_img_docs[0].meta["filename"] == "junk1.jpeg"
        assert more_img_docs[1].content == "<Image(junk2.jpeg)>"
        assert more_img_docs[1].meta["filename"] == "junk2.jpeg"
        assert more_img_docs[2].content == "<Image(junk3.jpeg)>"
        assert more_img_docs[2].meta["filename"] == "junk3.jpeg"

        # upload additional files
        # NOTE: file paths are relative to the execution directory (i.e., project root)
        even_more_docs = tmp_collection.upload_documents(
            [
                "sample_data/documents/StarCoder.pdf",
                "sample_data/documents/fluid.mp4",
                "sample_data/documents/hotd.txt",
            ]
        )
        assert len(even_more_docs) == 3

        pdf_doc = even_more_docs[0]
        assert pdf_doc.content == "<PDF(StarCoder.pdf)>"
        assert pdf_doc.document_id is not None
        assert pdf_doc.created_at is not None
        assert pdf_doc.updated_at is not None
        assert pdf_doc.collection_id == tmp_collection_id
        assert pdf_doc.object_url is not None
        # FIXME: lx_client.get() returns a 404 but httpx.get() returns a 200
        # assert pdf_doc.image is None
        assert pdf_doc.meta["filename"] == "StarCoder.pdf"
        assert pdf_doc.meta["storage_bucket"] == storage_bucket
        assert (
            pdf_doc.meta["storage_key"]
            == f"lexy_tests/collections/{tmp_collection_id}/documents/StarCoder.pdf"
        )
        assert pdf_doc.meta["size"] == 629980
        assert pdf_doc.meta["type"] == "pdf"
        assert pdf_doc.meta["content_type"] == "application/pdf"

        video_doc = even_more_docs[1]
        assert video_doc.content == "<Video(fluid.mp4)>"
        assert video_doc.document_id is not None
        assert video_doc.created_at is not None
        assert video_doc.updated_at is not None
        assert video_doc.collection_id == tmp_collection_id
        assert video_doc.object_url is not None
        # FIXME: lx_client.get() returns a 404 but httpx.get() returns a 200
        # assert video_doc.image is None
        assert video_doc.meta["filename"] == "fluid.mp4"
        assert video_doc.meta["storage_bucket"] == storage_bucket
        assert (
            video_doc.meta["storage_key"]
            == f"lexy_tests/collections/{tmp_collection_id}/documents/fluid.mp4"
        )
        assert video_doc.meta["size"] == 323778
        assert video_doc.meta["type"] == "video"
        assert video_doc.meta["content_type"] == "video/mp4"

        text_doc = even_more_docs[2]
        assert text_doc.content.startswith(
            "Viserys I Targaryen is the fifth king of the Targaryen dynasty to rule "
            "the Seven Kingdoms."
        )
        assert text_doc.document_id is not None
        assert text_doc.created_at is not None
        assert text_doc.updated_at is not None
        assert text_doc.collection_id == tmp_collection_id
        assert text_doc.object_url is not None
        # FIXME: lx_client.get() returns a 404 but httpx.get() returns a 200
        # assert text_doc.image is None
        assert text_doc.meta["filename"] == "hotd.txt"
        assert text_doc.meta["storage_bucket"] == storage_bucket
        assert (
            text_doc.meta["storage_key"]
            == f"lexy_tests/collections/{tmp_collection_id}/documents/hotd.txt"
        )
        assert text_doc.meta["size"] == 3144
        assert text_doc.meta["type"] == "text"
        assert text_doc.meta["content_type"] == "text/plain"

        # delete test documents
        response = lx_client.document.bulk_delete_documents(
            collection_name="test_upload_documents"
        )
        assert response.get("msg") == "Documents deleted"
        assert response.get("deleted_count") == 8

        # delete test collection
        response = lx_client.delete_collection(collection_name="test_upload_documents")
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == tmp_collection_id

    # TODO: run the equivalent tests for GCS
    @pytest.mark.asyncio
    async def test_document_urls(self, lx_client, settings, document_storage):
        thumbnail_dims = list(settings.IMAGE_THUMBNAIL_SIZES)[0]
        thumbnail_dims_str = f"{thumbnail_dims[0]}x{thumbnail_dims[1]}"

        tmp_collection = lx_client.create_collection(
            collection_name="test_document_urls", description="Test Document Urls"
        )
        assert tmp_collection.collection_name == "test_document_urls"
        assert tmp_collection.description == "Test Document Urls"
        assert tmp_collection.config == settings.COLLECTION_DEFAULT_CONFIG
        tmp_collection_id = tmp_collection.collection_id
        storage_service = tmp_collection.config.get("storage_service")
        assert storage_service == settings.DEFAULT_STORAGE_SERVICE
        storage_bucket = tmp_collection.config.get("storage_bucket")
        assert storage_bucket == settings.DEFAULT_STORAGE_BUCKET

        # upload documents to the test collection
        # NOTE: file paths are relative to the execution directory (i.e., project root)
        docs_uploaded = lx_client.upload_documents(
            files=[
                "sample_data/images/lexy.png",
            ],
            filenames=["testing-document-urls.png"],
            collection_name="test_document_urls",
        )
        assert len(docs_uploaded) == 1

        img_doc = docs_uploaded[0]
        assert img_doc.client == lx_client
        assert img_doc.content == "<Image(testing-document-urls.png)>"
        assert img_doc.document_id is not None
        assert img_doc.collection_id == tmp_collection_id
        assert img_doc.created_at is not None
        assert img_doc.updated_at is not None
        assert img_doc.object_url is not None

        # get document urls
        doc_urls = lx_client.document.get_document_urls(
            document_id=img_doc.document_id, expiration=3
        )
        # sample response:
        """
        {
            "object": "https://my-bucket.s3.amazonaws.com/path/to/object?...",
            "thumbnails": {
                "256x256": "https://my-bucket.s3.amazonaws.com/path/to/thumbnail?..."
            }
        }
        """

        # presigned object url
        assert "object" in doc_urls
        object_url = doc_urls["object"]
        assert object_url is not None
        if storage_service == "s3":
            assert object_url.startswith(f"https://{storage_bucket}.s3.")
        elif storage_service == "gcs":
            assert object_url.startswith(
                f"https://storage.googleapis.com/{storage_bucket}/"
            )
        object_key = (
            f"lexy_tests/collections/{tmp_collection_id}/documents/"
            f"testing-document-urls.png"
        )
        assert object_key in object_url

        # presigned thumbnail urls
        assert "thumbnails" in doc_urls
        assert thumbnail_dims_str in doc_urls["thumbnails"]
        if storage_service == "s3":
            assert doc_urls["thumbnails"][thumbnail_dims_str].startswith(
                f"https://{storage_bucket}.s3."
            )
        elif storage_service == "gcs":
            assert doc_urls["thumbnails"][thumbnail_dims_str].startswith(
                f"https://storage.googleapis.com/{storage_bucket}/"
            )
        thumbnail_key = (
            f"lexy_tests/collections/{tmp_collection_id}/thumbnails/"
            f"{thumbnail_dims_str}/testing-document-urls.png"
        )
        assert thumbnail_key in doc_urls["thumbnails"][thumbnail_dims_str]

        # check url expiration
        assert (
            presigned_url_is_expired(object_url, storage_service=storage_service)
            is False
        )
        assert (
            presigned_url_is_expired(
                doc_urls["thumbnails"][thumbnail_dims_str],
                storage_service=storage_service,
            )
            is False
        )
        await asyncio.sleep(3)
        assert (
            presigned_url_is_expired(object_url, storage_service=storage_service)
            is True
        )
        assert (
            presigned_url_is_expired(
                doc_urls["thumbnails"][thumbnail_dims_str],
                storage_service=storage_service,
            )
            is True
        )

        # delete test documents
        response = lx_client.document.bulk_delete_documents(
            collection_name="test_document_urls"
        )
        assert response.get("msg") == "Documents deleted"
        assert response.get("deleted_count") == 1

        # delete test collection
        response = lx_client.delete_collection(collection_name="test_document_urls")
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == tmp_collection_id

    @pytest.mark.asyncio
    async def test_upload_documents_to_collection_without_storage_bucket(
        self, lx_client, settings, document_storage
    ):
        # create a test collection without a storage bucket
        tmp_collection = lx_client.create_collection(
            collection_name="test_no_storage_bucket",
            description="Test No Storage Bucket",
            config={
                "store_files": True,
                "generate_thumbnails": True,
                "storage_service": settings.DEFAULT_STORAGE_SERVICE,
                "storage_bucket": None,
            },
        )
        assert tmp_collection.collection_name == "test_no_storage_bucket"
        assert tmp_collection.description == "Test No Storage Bucket"
        assert tmp_collection.config != settings.COLLECTION_DEFAULT_CONFIG
        tmp_collection_id = tmp_collection.collection_id
        storage_bucket = tmp_collection.config.get("storage_bucket")
        assert storage_bucket is None

        # upload documents to the test collection
        with pytest.raises(LexyAPIError) as exc_info:
            # NOTE: file paths are relative to the execution directory (i.e., project
            # root)
            lx_client.upload_documents(
                files=[
                    "sample_data/images/lexy.png",
                ],
                filenames=["testing-no-storage-bucket.png"],
                collection_name="test_no_storage_bucket",
            )
        assert isinstance(exc_info.value, LexyAPIError)
        assert exc_info.value.response.status_code == 400
        assert (
            exc_info.value.response.json()["detail"]
            == "Storage bucket not configured for this collection"
        )

        # delete test collection
        response = lx_client.delete_collection(collection_name="test_no_storage_bucket")
        assert response.get("msg") == "Collection deleted"
        assert response.get("collection_id") == tmp_collection_id


class TestDocumentModel:
    def test_document_model(self):
        doc = Document(content="Test Document Content")
        assert doc.content == "Test Document Content"
        assert doc.meta == {}
        assert doc.created_at is None
        assert doc.updated_at is None
        assert doc.collection_id is None
        assert doc.document_id is None
        assert repr(doc) == '<Document("Test Document Content")>'

        assert doc._client is None
        assert doc._image is None
        assert doc._urls is None

        # accessing object_url property without a client raises a ValueError
        with pytest.raises(ValueError) as exc_info:
            _ = doc.object_url
        assert isinstance(exc_info.value, ValueError)
        assert str(exc_info.value) == "API client has not been set."

        # first argument to Document sets the content attribute
        another_doc = Document("Another Document", meta={"key": "value"})
        assert another_doc.content == "Another Document"
        assert another_doc.meta == {"key": "value"}
        assert repr(another_doc) == '<Document("Another Document")>'
