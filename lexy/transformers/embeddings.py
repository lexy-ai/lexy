from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer

import torch
from sentence_transformers import SentenceTransformer


torch.set_num_threads(1)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@lexy_transformer(name="text.embeddings.minilm")
def text_embeddings(sentences: list[str | DocumentBase] | str | DocumentBase) -> torch.Tensor:
    """Embed sentences using SentenceTransformer.

    Args:
        sentences: A single sentence or a list of sentences to embed. Each sentence can be either a string or a
            DocumentBase instance.

    Returns:
        torch.Tensor: The embeddings of the provided sentences.
    """
    if isinstance(sentences, DocumentBase):
        sentences = sentences.content
    elif isinstance(sentences, list):
        sentences = [s.content if isinstance(s, DocumentBase) else s for s in sentences]
    return model.encode(sentences, batch_size=len(sentences))


@lexy_transformer(name="embeddings.get_chunks")
def get_chunks(text, chunk_size=384) -> list[str]:
    """
    Split text into chunks of size chunk_size.

    Args:
        text: text to split
        chunk_size: chunk size in number of tokens

    Returns:
        list[str]: list of chunks

    Examples:
        >>> get_chunks("This is a test", chunk_size=2)
        ["This is", "a test"]
    """
    chunks = []
    chunk = []
    chunk_length = 0
    words = text.split(' ')

    for word in words:
        tokens = model.tokenize(word)
        token_length = len(tokens)

        if chunk_length + token_length <= chunk_size:
            chunk.append(word)
            chunk_length += token_length
        else:
            chunks.append(' '.join(chunk))
            chunk = [word]
            chunk_length = token_length

    return chunks


@lexy_transformer(name="embeddings.just_split")
def just_split(text: str, n_times=3) -> list:
    return text.split(' ', n_times)
