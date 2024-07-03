import time

from lexy_py.client import LexyClient
from lexy_py.binding.models import Binding
from lexy_py.collection.models import Collection
from lexy_py.index.models import Index
from lexy_py.transformer.models import Transformer


class TestTutorial:
    def test_root(self, lx_client):
        response = lx_client.get("/")
        assert response.status_code == 200
        assert response.json() == {"Say": "Hello!"}

    # make sure that default collection is empty
    def test_bulk_delete_documents(self, lx_client):
        response = lx_client.bulk_delete_documents(collection_name="default")
        assert response.get("msg") == "Documents deleted"

        default_collection = lx_client.get_collection(collection_name="default")
        docs = default_collection.list_documents()
        assert len(docs) == 0

    def test_tutorial(self, lx_client, celery_app, celery_worker):
        # Introduction

        # adding documents to the default collection
        first_doc, starlink_doc, latent_space_doc = lx_client.add_documents(
            [
                {"content": "This is my first document! It's great!"},
                {
                    "content": "Starlink is a satellite internet constellation "
                    "operated by American aerospace company SpaceX, "
                    "providing coverage to over 60 countries."
                },
                {
                    "content": "A latent space is an embedding of a set of items "
                    "within a manifold in which items resembling each "
                    "other are positioned closer to one another."
                },
            ]
        )

        # wait for the celery worker to finish the embedding tasks
        time.sleep(2)

        # query the default index
        response = lx_client.query_index("what is deep learning?")
        assert len(response) == 3

        # check that all documents are in the response
        document_ids = [doc["document_id"] for doc in response]
        assert first_doc.document_id in document_ids
        assert starlink_doc.document_id in document_ids
        assert latent_space_doc.document_id in document_ids

        # check that the latent space document is the top result
        assert response[0]["document_id"] == latent_space_doc.document_id

        # Example: Famous biographies

        # create a new collection
        bios = lx_client.create_collection("bios", description="Famous Biographies")
        assert isinstance(bios, Collection)
        assert isinstance(bios.client, LexyClient)
        assert bios.collection_name == "bios"
        assert bios.description == "Famous Biographies"

        # show empty collection
        docs = bios.list_documents()
        assert len(docs) == 0

        # add documents to the bios collection
        docs_added = bios.add_documents(
            [
                {
                    "content": "Stephen Curry is an American professional basketball "
                    "player for the Golden State Warriors."
                },
                {
                    "content": "Dwayne 'The Rock' Johnson is a well-known actor, "
                    "former professional wrestler, and businessman."
                },
                {
                    "content": "Taylor Swift is a singer known for her songwriting, "
                    "musical versatility, and artistic reinventions."
                },
            ]
        )
        assert len(docs_added) == 3
        bio_steph_curry = docs_added[0]
        bio_the_rock = docs_added[1]
        bio_taylor_swift = docs_added[2]

        # check available transformers
        transformers = lx_client.transformers
        assert len(transformers) > 0
        assert isinstance(transformers[0], Transformer)
        transformer_ids = [t.transformer_id for t in transformers]
        assert "text.embeddings.minilm" in transformer_ids

        # create a new index for the bios collection
        index_fields = {
            "bio_embedding": {
                "type": "embedding",
                "extras": {"dims": 384, "model": "text.embeddings.minilm"},
            }
        }
        index = lx_client.create_index(
            index_id="bios_index",
            description="Biography embeddings",
            index_fields=index_fields,
        )
        assert isinstance(index, Index)
        assert isinstance(index.client, LexyClient)
        assert index.index_id == "bios_index"
        assert index.description == "Biography embeddings"

        # create a binding
        binding = lx_client.create_binding(
            collection_name="bios",
            transformer_id="text.embeddings.minilm",
            index_id="bios_index",
        )
        assert isinstance(binding, Binding)
        assert isinstance(binding.client, LexyClient)
        assert binding.collection.collection_name == "bios"
        assert binding.index.index_id == "bios_index"
        assert binding.transformer.transformer_id == "text.embeddings.minilm"
        assert binding.status == "on"
        assert "lexy_index_fields" in binding.transformer_params
        assert set(binding.index.index_fields.keys()) == set(
            binding.transformer_params["lexy_index_fields"]
        )

        # wait for the celery worker to finish the embedding tasks
        time.sleep(2)

        # query the bios index
        response = index.query(
            query_text="famous artists", query_field="bio_embedding", k=3
        )
        assert len(response) == 3

        # check that all documents are in the response
        document_ids = [doc["document_id"] for doc in response]
        assert bio_steph_curry.document_id in document_ids
        assert bio_the_rock.document_id in document_ids
        assert bio_taylor_swift.document_id in document_ids

        # check that the taylor swift document is the top result
        assert response[0]["document_id"] == bio_taylor_swift.document_id
        # check that the rock document is the second result
        assert response[1]["document_id"] == bio_the_rock.document_id

        # add a new document
        doc_added = bios.add_documents(
            [
                {
                    "content": "Beyoncé is a singer and songwriter recognized for her "
                    "boundary-pushing artistry, vocals, and performances."
                }
            ]
        )
        assert len(doc_added) == 1
        beyonce_doc = doc_added[0]

        # wait for the celery worker to finish the embedding tasks
        time.sleep(0.5)

        # query the bios index again
        response = index.query(
            query_text="famous artists", query_field="bio_embedding", k=3
        )
        assert len(response) == 3
        document_ids = [doc["document_id"] for doc in response]
        assert beyonce_doc.document_id in document_ids

        # check that the taylor swift document is the top result
        assert response[0]["document_id"] == bio_taylor_swift.document_id
        # check that the beyonce document is the second result
        assert response[1]["document_id"] == beyonce_doc.document_id
        # check that the rock document is the third result
        assert response[2]["document_id"] == bio_the_rock.document_id
