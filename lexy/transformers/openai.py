import logging
import os

from openai import OpenAI

from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer


logger = logging.getLogger(__name__)
if os.environ.get("OPENAI_API_KEY"):
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
else:
    openai_client = None
    logger.warning("OPENAI_API_KEY not set; cannot use OpenAI API")


@lexy_transformer(name="text.embeddings.openai")
def text_embeddings(
    text: list[str | DocumentBase] | str | DocumentBase, *, model: str, **kwargs
) -> list[list[float]] | list[float]:
    """Embed text using the OpenAI API.

    Any additional keyword arguments are passed to the client's
    :func:`OpenAI.embeddings.create` method.

    Args:
        text: A single string or DocumentBase instance, or a list of strings or
            DocumentBase instances to embed.
        model: The OpenAI model to use for embeddings. Can be one of
            "text-embedding-ada-002", "text-embedding-3-small", or
            "text-embedding-3-large".

    Keyword Args:
        encoding_format: The format to return the embeddings in. Can be either `float`
            or `base64 <https://pypi.org/project/pybase64/>`__.
        dimensions: The number of dimensions for the resulting output embeddings. Only
            supported in "text-embedding-3" and later models.
        user: A unique identifier representing your end-user, which can help OpenAI to
            monitor and detect abuse.
        extra_headers: Send extra headers
        extra_query: Add additional query parameters to the request
        extra_body: Add additional JSON properties to the request
        timeout: Override the client-level default timeout for this request, in seconds

    Returns:
        list[list[float]] | list[float]: The embeddings of the provided text.
    """
    if not openai_client:
        raise Exception("OPENAI_API_KEY not set; cannot use OpenAI API")

    if isinstance(text, DocumentBase):
        text = text.content
    elif isinstance(text, list):
        text = [s.content if isinstance(s, DocumentBase) else s for s in text]

    api_response = openai_client.embeddings.create(model=model, input=text, **kwargs)

    if isinstance(text, list):
        return [e.embedding for e in api_response.data]
    else:
        return api_response.data[0].embedding


@lexy_transformer(name="text.embeddings.openai-3-small")
def text_embeddings_3_small(
    text: list[str | DocumentBase] | str | DocumentBase, **kwargs
) -> list[list[float]] | list[float]:
    """Embed text using OpenAI's "text-embedding-3-small" model.

    This runs :func:`lexy.transformers.openai.text_embeddings` with
    `model="text-embedding-3-small"`.

    Args:
        text: A single string or DocumentBase instance, or a list of strings or
            DocumentBase instances to embed.

    Returns:
        list[list[float]] | list[float]: The embeddings of the provided text.

    See Also:
        :func:`lexy.transformers.openai.text_embeddings` for additional keyword args.
    """
    return text_embeddings(text, model="text-embedding-3-small", **kwargs)


@lexy_transformer(name="text.embeddings.openai-3-large")
def text_embeddings_3_large(
    text: list[str | DocumentBase] | str | DocumentBase, **kwargs
) -> list[list[float]] | list[float]:
    """Embed text using OpenAI's "text-embedding-3-large" model.

    This runs :func:`lexy.transformers.openai.text_embeddings` with
    `model="text-embedding-3-large"`.

    Args:
        text: A single string or DocumentBase instance, or a list of strings or
            DocumentBase instances to embed.

    Returns:
        list[list[float]] | list[float]: The embeddings of the provided text.

    See Also:
        :func:`lexy.transformers.openai.text_embeddings` for additional keyword args.
    """
    return text_embeddings(text, model="text-embedding-3-large", **kwargs)


@lexy_transformer(name="text.embeddings.openai-ada-002")
def text_embeddings_ada_002(
    text: list[str | DocumentBase] | str | DocumentBase, **kwargs
) -> list[list[float]] | list[float]:
    """Embed text using OpenAI's "text-embedding-ada-002" model.

    This runs :func:`lexy.transformers.openai.text_embeddings` with
    `model="text-embedding-ada-002"`.

    Args:
        text: A single string or DocumentBase instance, or a list of strings or
            DocumentBase instances to embed.

    Returns:
        list[list[float]] | list[float]: The embeddings of the provided text.

    See Also:
        :func:`lexy.transformers.openai.text_embeddings` for additional keyword args.
    """
    return text_embeddings(text, model="text-embedding-ada-002", **kwargs)
