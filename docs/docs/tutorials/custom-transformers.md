# Custom transformers

This tutorial shows how to create custom transformers for use in your data pipelines.


Up until now, we've only used the default transformers included in Lexy. These include common methods for embedding text
and images. But we'll often want to apply custom transformations to our documents based on metadata or our own custom 
logic. In this tutorial, we'll create our own transformer for parsing comments from source code.


## Add transformer code

Add your transformer code in a new module with the path `lexy.transformers.<your_module>`. Assuming your module is 
called `code`, your project should have the following structure:

```hl_lines="4"
lexy
├── transformers
    ├── __init__.py
    ├── code.py
    ├── counter.py
    ├── embeddings.py
    ├── multimodal.py
    └── openai.py
```

And your file `code.py` should look something like this:

```python title="lexy/transformers/code.py"
from lexy.models.document import Document
from lexy.transformers import lexy_transformer


def parse_code(content):
    # just an example - replace with your own logic
    return [
        {'text': 'my comment', 'line_no': 1, 'filename': 'example.py'}
    ]


@lexy_transformer(name='code.extract_comments.v1')  # (1)!
def get_comments(doc: Document) -> list[dict]:
    comments = []
    for c in parse_code(doc.content):
        comments.append({
            'comment_text': c['text'],
            'comment_meta': {
                'line_no': c['line_no'],
                'filename': c['filename']
            }
        })
    return comments
```

1.  The `@lexy_transformer` decorator registers your function as a transformer. The `name` argument is the transformer 
    ID. This is how you'll refer to your transformer when creating bindings. The `name` should be unique across all 
    transformers.

## Install optional dependencies

Make sure to install any dependencies required for your custom transformer code.

In development, you can install your dependencies using `docker exec`. This will be temporary (for the life of the 
docker container), but makes it easy to work with your packages in development.

```bash
docker exec lexy-server pip install <your_package>
docker exec lexy-celeryworker pip install <your_package>
```

In production, you'll want to update `pyproject.toml` to include your package in the list of `lexy_transformers` 
extras.

```toml hl_lines="6 9" title="pyproject.toml"
[tool.poetry.dependencies]
...
# optional dependencies
transformers = { version = "^4.33.1", extras = ["torch"], optional = true}
sentence-transformers = { version = "^2.2.2", optional = true}
<your_package> = { version = "<version>", optional = true}

[tool.poetry.extras]
lexy_transformers = ["transformers", "sentence-transformers", "<your_package>"]
```

## Update configuration

In `lexy.core.config`, update the values for `LEXY_SERVER_TRANSFORMER_IMPORTS` and `LEXY_WORKER_TRANSFORMER_IMPORTS` 
to include your new module.

```python hl_lines="8 15" title="lexy/core/config.py"
# code omitted above...

class AppSettings(BaseSettings):

    # other settings...
    
    LEXY_SERVER_TRANSFORMER_IMPORTS: set[str] = { # (1)!
        'lexy.transformers.code',  # add your module here
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
        'lexy.transformers.openai',
    }
    LEXY_WORKER_TRANSFORMER_IMPORTS: set[str] = { # (2)!
        'lexy.transformers.code',  # add your module here
        'lexy.transformers.counter',
        'lexy.transformers.embeddings',
        'lexy.transformers.multimodal',
        'lexy.transformers.openai',
    }
    
    # more settings...
```

1.  These modules are imported by the Lexy server at startup. If the transformer requires significant resources, you 
    should omit it from this list and instead import it in the worker.
2.  These modules are imported each time a worker is created or restarted.

Then restart the Lexy server and worker for the updated configuration to take effect:

```bash
docker compose restart lexyserver lexyworker
```

## Create transformer

Finally, create your transformer so that it's stored in the database and available to the Lexy server. You can do this 
by calling the [`create_transformer`](../reference/lexy_py/transformer.md#lexy_py.transformer.client.TransformerClient.add_transformer) 
method.

```python
from lexy_py import LexyClient

lx = LexyClient()

lx.create_transformer(
    transformer_id='code.extract_comments.v1', 
    path='lexy.transformers.code.get_comments',
    description='Parse comments and docstrings.'
)
```

```{ .text .no-copy .result #code-output }
<Transformer('code.extract_comments.v1', description='Parse comments and docstrings')>
```

Now when you call the [`.transformers`](../reference/lexy_py/client.md#lexy_py.client.LexyClient.transformers) property of the Lexy client, you'll be able to see your transformer listed. 

```python
lx.transformers
```

```{ .text .no-copy .result #code-output }
[<Transformer('image.embeddings.clip', description='Embed images using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.clip', description='Embed text using 'openai/clip-vit-base-patch32'.')>,
 <Transformer('text.embeddings.minilm', description='Text embeddings using "sentence-transformers/all-MiniLM-L6-v2"')>,
 <Transformer('text.embeddings.openai-3-large', description='Text embeddings using OpenAI's "text-embedding-3-large" model')>,
 <Transformer('text.embeddings.openai-3-small', description='Text embeddings using OpenAI's "text-embedding-3-small" model')>,
 <Transformer('text.embeddings.openai-ada-002', description='OpenAI text embeddings using model text-embedding-ada-002')>,
 <Transformer('code.extract_comments.v1', description='Parse comments and docstrings')>]
```

You're now ready to use your custom transformer to process documents!

### Testing with sample documents

You can use the [`transform_document`](../reference/lexy_py/transformer.md#lexy_py.transformer.client.TransformerClient.transform_document) 
method of the `Transformer` class to test your transformer on sample documents.

```python
code_transformer = lx.get_transformer('code.extract_comments.v1')

sample_doc = {
    'content': 'print("hello world")', 
    'meta': {
      'filename': 'example.py'
    }
}

code_transformer.transform_document(sample_doc)
```

```{ .text .no-copy .result #code-output }
{'task_id': '65ecd2f7-bac4-4747-9e65-a6d21a72f585', 
 'result': [{'comment_text': 'my comment', 'comment_meta': {'line_no': 1, 'filename': 'example.py'}}]}
```
