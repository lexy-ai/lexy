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
    {"content": "This is a test document"},
    {"content": "This is another one!"},
])
```

### Query index

```python
lexy.index.query_index("test query", "default_text_embeddings", k=5)
```

## Testing

```bash
pytest sdk-python
```
