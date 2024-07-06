# Lexy Python SDK

This is the Python SDK for [Lexy](https://pypi.org/project/lexy/). For detailed
documentation and tutorials, see the [Lexy documentation](https://getlexy.com).

## Usage

### Init client

```python
from lexy_py import LexyClient

lx = LexyClient()
```

### Add documents

```python
lx.add_documents([
    {"content": "This is a test document"},
    {"content": "This is another one!"},
])
```

### Query index

```python
lx.query_index("test query", index_id="default_text_embeddings", k=5)
```
