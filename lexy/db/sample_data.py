default_data = {
    "collections": [
        {"collection_name": "default", "description": "Default collection"},
        {"collection_name": "code", "description": "Github code repos"},
    ],
    "transformers": [
        {
            "transformer_id": "text.embeddings.minilm",
            "path": "lexy.transformers.embeddings.text_embeddings",
            "description": 'Text embeddings using "sentence-transformers/all-MiniLM-L6-v2"',
        },
        {
            "transformer_id": "text.embeddings.clip",
            "path": "lexy.transformers.multimodal.text_embeddings_clip",
            "description": 'Text embeddings using "openai/clip-vit-base-patch32"',
        },
        {
            "transformer_id": "image.embeddings.clip",
            "path": "lexy.transformers.multimodal.image_embeddings_clip",
            "description": 'Image embeddings using "openai/clip-vit-base-patch32"',
        },
        {
            "transformer_id": "text.embeddings.openai",
            "path": "lexy.transformers.openai.text_embeddings",
            "description": "Text embeddings using the OpenAI API",
        },
        {
            "transformer_id": "text.embeddings.openai-ada-002",
            "path": "lexy.transformers.openai.text_embeddings_ada_002",
            "description": 'Text embeddings using OpenAI\'s "text-embedding-ada-002" model',
        },
        {
            "transformer_id": "text.embeddings.openai-3-small",
            "path": "lexy.transformers.openai.text_embeddings_3_small",
            "description": 'Text embeddings using OpenAI\'s "text-embedding-3-small" model',
        },
        {
            "transformer_id": "text.embeddings.openai-3-large",
            "path": "lexy.transformers.openai.text_embeddings_3_large",
            "description": 'Text embeddings using OpenAI\'s "text-embedding-3-large" model',
        },
        {
            "transformer_id": "text.counter.word_counter",
            "path": "lexy.transformers.counter.word_counter",
            "description": "Returns count of words and the longest word",
        },
    ],
    "indexes": [
        {
            "index_id": "default_text_embeddings",
            "description": "Text embeddings for default collection",
            "index_table_schema": {
                "title": "DefaultTextEmbeddings",
                "type": "object",
                "properties": {
                    "document_id": {
                        "title": "Document Id",
                        "type": "string",
                        "format": "uuid",
                    },
                    "embedding": {
                        "title": "Embedding",
                        "type": "array",
                        "items": {"type": "number"},
                    },
                    "text": {"title": "Text", "type": "string"},
                    "meta": {"title": "Meta", "default": {}, "type": "object"},
                    "custom_id": {"title": "Custom Id", "type": "string"},
                    "embedding_id": {
                        "title": "Embedding Id",
                        "type": "string",
                        "format": "uuid",
                    },
                    "created_at": {
                        "title": "Created At",
                        "type": "string",
                        "format": "date-time",
                    },
                    "updated_at": {
                        "title": "Updated At",
                        "type": "string",
                        "format": "date-time",
                    },
                    "task_id": {"title": "Task Id", "type": "string", "format": "uuid"},
                },
                "required": ["document_id", "embedding", "created_at", "updated_at"],
            },
            "index_fields": {
                "embedding": {
                    "type": "embedding",
                    "extras": {"dims": 384, "model": "text.embeddings.minilm"},
                },
                "text": {"type": "string", "optional": True},
            },
        }
    ],
    "bindings": [
        {
            "collection_name": "default",
            "transformer_id": "text.embeddings.minilm",
            "index_id": "default_text_embeddings",
            "description": "Default binding",
            "execution_params": {},
            "transformer_params": {"lexy_index_fields": ["embedding"]},
            "filters": {},
            "status": "on",
        }
    ],
}

sample_docs = {
    "default_collection_sample_docs": [
        {
            "content": "This is my first document! It's great!",
            "collection_name": "default",
        },
        {
            "content": "Starlink is a satellite internet constellation operated by American aerospace company SpaceX, "
            "providing coverage to over 60 countries.",
            "collection_name": "default",
        },
        {
            "content": "A latent space is an embedding of a set of items within a manifold in which items resembling "
            "each other are positioned closer to one another.",
            "collection_name": "default",
        },
    ],
    "code_collection_sample_docs": [
        {
            "collection_name": "code",
            "content": "import this",
            "meta": {
                "filename": "main.py",
                "file_extension": "py",
                "language": "python",
            },
        },
        {
            "collection_name": "code",
            "content": "def multiply(a, b):"
            "    return a * b"
            ""
            ""
            "if __name__ == '__main__':"
            "    print(multiply(2, 3))",
            "meta": {
                "filename": "multiply.py",
                "file_extension": "py",
                "language": "python",
            },
        },
    ],
}
