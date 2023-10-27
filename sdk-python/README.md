# Lexy Python SDK

This is the Python SDK for Lexy.

## Usage

### Initiate client

```python
from lexy_py.client import LexyClient

lexy = LexyClient()
```

### Add documents

```python
lexy.document.add_documents([
    {"title": "doc1", "content": "This is a test document"},
    {"title": "My second doc", "content": "This is another one!"},
])
```

### Query index

```python
lexy.index.query_index("default_text_embeddings", "test query", k=5)
```

## Testing

```bash
pytest sdk-python
```
