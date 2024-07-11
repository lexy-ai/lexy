# Custom transformers

This tutorial shows how to create custom transformers for use in your data pipelines.


Up until now, we've only used the default transformers included in Lexy. These include common methods for embedding text
and images. But we'll often want to apply custom transformations to our documents based on metadata or our own custom
logic. In this tutorial, we'll create our own transformer for parsing comments from source code.

!!! info
    Currently, there is no clear distinction between "transformers" and "pipelines."
    They can be used interchangeably. This will change in upcoming versions of Lexy,
    when we introduce additional functionality for pipelines.

## Project structure

Let's take a look at our project structure. If we're working inside the Lexy repository,
the structure will look like this:

```shell
lexy
├── ...
├── pipelines  # (1)!
│   ├── __init__.py
│   └── requirements.txt  # (2)!
```

1.  This is the Lexy pipelines directory, defined by the environment variable
    `PIPELINE_DIR`. The modules in this directory are imported and run by the
    `lexyworker` container.
2.  Extra requirements for your pipelines or custom transformers. These packages will
    be installed whenever you restart the `lexyworker` container.

And if you're using Lexy inside your own project, the structure might look like the one
in the [Quickstart](../quickstart.md#building-with-lexy) guide. Either way, you'll have
a `pipelines` directory where you can store your custom transformers.


## Add transformer logic

Let's add a new module in the pipelines directory called `code`.

```hl_lines="5"
lexy
├── ...
├── pipelines
│   ├── __init__.py
│   ├── code.py
│   └── requirements.txt
```

And let's add the following to our file `code.py`:

```python title="pipelines/code.py"
from lexy.models import Document
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

1.  The `@lexy_transformer` decorator registers your function as a transformer. The
    `name` argument is the transformer ID. This is how you'll refer to your transformer
    when creating bindings. The `name` should be unique across all transformers.

## Install optional dependencies

Make sure to install any package dependencies required for your custom transformer code.
You can do this by adding the package to the `requirements.txt` file in the `pipelines`
directory and restarting the `lexyworker` container.

```plaintext hl_lines="2-3" title="pipelines/requirements.txt"
# Extra package requirements for pipelines
tree-sitter==0.20.4
tree-sitter-languages==1.8.0
```

Then restart the `lexyworker` container:

```bash
docker compose restart lexyworker
```

You can check the `lexyworker` container logs to see that the packages are being
installed correctly. You can also check the `pip install` logs by running:

```Shell
docker compose exec lexyworker tail /var/log/lexy-pip.log
```

## Create transformer

Finally, create your transformer so that it's stored in the database and available to
the Lexy server. You can do this by calling the [`create_transformer`](../reference/lexy_py/transformer.md#lexy_py.transformer.client.TransformerClient.create_transformer) method.

```python
from lexy_py import LexyClient

lx = LexyClient()

lx.create_transformer(
    transformer_id='code.extract_comments.v1',
    description='Parse comments and docstrings.'
)
```

```{ .text .no-copy .result #code-output }
<Transformer('code.extract_comments.v1', description='Parse comments and docstrings')>
```

Now when you call the [`.transformers`](../reference/lexy_py/client.md#lexy_py.client.LexyClient.transformers) property of the Lexy client, you'll be
able to see your transformer listed.

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

You can use the [`Transformer.transform_document`](../reference/lexy_py/transformer.md#lexy_py.transformer.models.Transformer.transform_document)
method to test your transformer on a sample document.

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

If your transformer code produces an error, you'll see the error message and traceback
in the response.


## Updating transformer logic

The transformer we've created above is just an example. You may have also noticed that
we installed the `tree-sitter` and `tree-sitter-languages` packages in
`requirements.txt`, but we aren't using them.

Let's update `code.py` to actually parse comments from a variety of source code files.

```python title="pipelines/code.py"
import tree_sitter_languages

from lexy.models import Document
from lexy.transformers import lexy_transformer
from lexy.transformers.embeddings import text_embeddings


lang_from_ext = {
    'cc': 'cpp',
    'h': 'cpp',
    'py': 'python',
    'ts': 'typescript',
    'tsx': 'tsx',
}

COMMENT_PATTERN_CPP = "(comment) @comment"
COMMENT_PATTERN_PY = """
    (module . (comment)* . (expression_statement (string)) @module_doc_str)

    (class_definition
        body: (block . (expression_statement (string)) @class_doc_str))

    (function_definition
        body: (block . (expression_statement (string)) @function_doc_str))
"""
COMMENT_PATTERN_TS = "(comment) @comment"
COMMENT_PATTERN_TSX = "(comment) @comment"

comment_patterns = {
    'cpp': COMMENT_PATTERN_CPP,
    'python': COMMENT_PATTERN_PY,
    'typescript': COMMENT_PATTERN_TS,
    'tsx': COMMENT_PATTERN_TSX
}


@lexy_transformer(name='code.extract_comments.v1')
def get_comments(doc: Document) -> list[dict]:
    lang = lang_from_ext.get(doc.meta['file_ext'].replace('.', ''))
    comment_pattern = comment_patterns.get(lang, None)

    if comment_pattern is None:
        return []

    parser = tree_sitter_languages.get_parser(lang)
    language = tree_sitter_languages.get_language(lang)

    tree = parser.parse(bytes(doc.content, "utf-8"))
    root = tree.root_node

    query = language.query(comment_pattern)
    matches = query.captures(root)
    comments = []
    for m, name in matches:
        comment_text = m.text.decode('utf-8')
        c = {
            'comment_text': comment_text,
            'comment_embedding': text_embeddings(comment_text),
            'comment_meta': {
                'start_point': m.start_point,
                'end_point': m.end_point,
                'type': name
            }
        }
        comments.append(c)
    return comments
```

Our updated code now takes a `Document` object and uses the file extension to determine
the appropriate language parser and comment patterns. It then parses comment text and
metadata, and also embeds the comment text using the `MiniLM` transformer.

When we update the transformer code, the `lexyworker` container will automatically
restart and load the new code. Let's test the updated transformer using a slightly more
complex sample document.

```python
sample_content = (
    '""" This is a module docstring. """\n'
    '\n'
    '# This is a comment\n'
    'class MyClass:\n'
    '   """ This is a class docstring. """\n'
    '   def __init__():\n'
    '       # TODO: implement this\n'
    '       pass\n'
    ''
)

sample_doc = {
    'content': sample_content,
    'meta': {
        'file_name': 'example.py',
        'file_ext': '.py'
    }
}

code_transformer.transform_document(sample_doc)
```

```{ .text .no-copy .result #code-output }
{'task_id': '48666991-308d-47ea-badf-3dd62f7b3778',
 'result': [{'comment_text': '""" This is a module docstring. """',
   'comment_embedding': [-0.028629321604967117, 0.10635735094547272, ..., 0.01644347794353962],
   'comment_meta': {'start_point': [0, 0],
    'end_point': [0, 35],
    'type': 'module_doc_str'}},
  {'comment_text': '""" This is a class docstring. """',
   'comment_embedding': [-0.027630936354398727, 0.1391005963087082, ..., 0.07976623624563217],
   'comment_meta': {'start_point': [4, 3],
    'end_point': [4, 37],
    'type': 'class_doc_str'}}]}
```

We can continue to iterate on our transformer code and test it on sample documents. Once
we're ready, we can create an index for storing the transformer output, and then create
a binding to apply the transformer to a collection of documents.
