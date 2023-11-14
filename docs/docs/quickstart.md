# Quickstart


## Getting started

If you're working in Python, you can use `lexy-py` to instantiate a client. 

```python
from lexy_py import LexyClient

lexy = LexyClient()
lexy.info()
```

## Collections


=== "Python"

    ```python
    lexy.get_collections()
    ```
=== "Shell"

    ```bash
    curl -X 'GET' \
        'http://localhost:9900/api/collections' \
        -H 'accept: application/json'
    ```


## Documents


=== "Python"

    ```python
    lexy.list_documents()
    ```
=== "Shell"

    ```bash
    curl -X 'GET' \
        'http://localhost:9900/api/documents?collection_id=default' \
        -H 'accept: application/json'
    ```
