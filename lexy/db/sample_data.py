sample_data = {
    "default_collection": {
        "collection_id": "default",
        "description": "Default collection"
    },
    "code_collection": {
        "collection_id": "code",
        "description": "Github code repos"
    },
    "document_1": {
        "title": "My first doc",
        "content": "This is my first document! It's great!",
        "collection_id": "default"
    },
    "document_2": {
        "title": "Another doc",
        "content": "Meh. This one is just ok.",
        "collection_id": "default"
    },
    "document_3": {
        "title": "SpaceX Starlink",
        "content": "Starlink is a satellite internet constellation operated by American aerospace company SpaceX, "
                   "providing coverage to over 60 countries.",
        "collection_id": "default"
    },
    "document_4": {
        "title": "Latent Space",
        "content": "A latent space, also known as a latent feature space or embedding space, is an embedding of a set "
                   "of items within a manifold in which items resembling each other are positioned closer to one "
                   "another.",
        "collection_id": "default"
    },
    "document_5": {
        "title": "main.py",
        "content": "import this",
        "collection_id": "code",
        "meta": {
            "language": "python",
            "file_extension": "py"
        }
    },
    "document_6": {
        "title": "multiply.py",
        "content": "def multiply(a, b):"
                   "    return a * b"
                   ""
                   ""
                   "if __name__ == '__main__':"
                   "    print(multiply(2, 3))",
        "collection_id": "code",
        "meta": {
            "language": "python",
            "file_extension": "py"
        }
    },
    "transformer_1": {
        "transformer_id": "text.embeddings.minilm",
        "description": "Text embeddings using Hugging Face model 'sentence-transformers/all-MiniLM-L6-v2'",
        "code": """import torch
from sentence_transformers import SentenceTransformer
torch.set_num_threads(1)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                       
def transform(document):
    return model.encode([document.content], batch_size=len([document.content]))"""
    },
    "index_1": {
        "index_id": "default_text_embeddings",
        "description": "Text embeddings for default collection",
        "index_table_schema": {
            "title": "DefaultTextEmbeddings",
            "type": "object",
            "properties": {
                "document_id": {
                    "title": "Document Id",
                    "type": "string",
                    "format": "uuid"
                },
                "embedding": {
                    "title": "Embedding",
                    "type": "array",
                    "items": {
                        "type": "number"
                    }
                },
                "text": {
                    "title": "Text",
                    "type": "string"
                },
                "meta": {
                    "title": "Meta",
                    "default": {},
                    "type": "object"
                },
                "custom_id": {
                    "title": "Custom Id",
                    "type": "string"
                },
                "embedding_id": {
                    "title": "Embedding Id",
                    "type": "string",
                    "format": "uuid"
                },
                "created_at": {
                    "title": "Created At",
                    "type": "string",
                    "format": "date-time"
                },
                "updated_at": {
                    "title": "Updated At",
                    "type": "string",
                    "format": "date-time"
                },
                "task_id": {
                    "title": "Task Id",
                    "type": "string",
                    "format": "uuid"
                }
            },
            "required": [
                "document_id",
                "embedding",
                "created_at",
                "updated_at"
            ]
        },
        "index_fields": {
            "embedding": {
                "type": "embedding",
                "extras": {
                    "dims": 384,
                    "distance": "cos"
                }
            },
            "text": {
                "type": "string",
                "optional": True
            }
        }
    },
    "binding_1": {
        "collection_id": "default",
        "transformer_id": "text.embeddings.minilm",
        "index_id": "default_text_embeddings",
        "description": "Default transformer-index binding",
        "execution_params": {},
        "transformer_params": {},
        "filters": {}
    }
}
