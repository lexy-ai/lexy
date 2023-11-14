# Quickstart


## Getting started

If you're working in Python, you can use `lexy-py` to instantiate a client. 

```python
from lexy_py import LexyClient

lexy = LexyClient()
lexy.info()
```

## Collections


=== ":material-language-python: Python"

    ```python
    lexy.list_collections()
    ```
    ``` { .python .no-copy title="Output" }
    [<Collection('default', description='Default collection')>,
     <Collection('code', description='Github code repos')>]
    ```
=== ":simple-gnubash: Shell"

    ```shell
    curl -X 'GET' \
        'http://localhost:9900/api/collections' \
        -H 'accept: application/json'
    ```
    ``` { .json .no-copy title="Output" }
    [
      {
        "collection_id": "default",
        "description": "Default collection",
        "created_at": "2023-11-03T21:40:23.941197+00:00",
        "updated_at": "2023-11-03T21:40:23.941197+00:00"
      },
      {
        "collection_id": "code",
        "description": "Github code repos",
        "created_at": "2023-11-03T21:40:23.941197+00:00",
        "updated_at": "2023-11-03T21:40:23.941197+00:00"
      }
    ]
    ```


## Documents


=== ":material-language-python: Python"

    ```python
    lexy.list_documents(collection_id='code')
    ```
    ???+ "Output"
        ``` { .python .no-copy }
        [<Document("import this")>,
         <Document("def multiply(a, b): return a * bif __name__ == '__main__': print(multiply(2, 3))")>]
        ```
=== ":simple-gnubash: Shell"

    ```shell
    curl -X 'GET' \
        'http://localhost:9900/api/documents?collection_id=code' \
        -H 'accept: application/json'
    ```
    ???+ Output
        ``` { .json .no-copy }
        [
          {
            "meta": {
              "filename": "main.py",
              "language": "python",
              "file_extension": "py"
            },
            "document_id": "20984c80-2a3c-475d-af59-45864762fc73",
            "collection_id": "code",
            "content": "import this",
            "created_at": "2023-11-03T21:40:23.948372+00:00",
            "updated_at": "2023-11-03T21:40:23.948372+00:00"
          },
          {
            "meta": {
              "filename": "multiply.py",
              "language": "python",
              "file_extension": "py"
            },
            "document_id": "1a9317e5-0d1f-4c7f-b731-42bddf0f4c98",
            "collection_id": "code",
            "content": "def multiply(a, b):    return a * bif __name__ == '__main__':    print(multiply(2, 3))",
            "created_at": "2023-11-03T21:40:23.948372+00:00",
            "updated_at": "2023-11-03T21:40:23.948372+00:00"
          }
        ]
        ```
