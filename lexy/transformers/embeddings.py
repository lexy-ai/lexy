from celery import shared_task

import torch
from numpy import ndarray
from sentence_transformers import SentenceTransformer
from torch import Tensor

torch.set_num_threads(1)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


@shared_task(name="lexy.transformers.embeddings.text_embeddings")
def text_embeddings(sentences: list[str]) -> torch.Tensor:
    """ Embed sentences using SentenceTransformer.

    Args:
        sentences: list of sentences to embed

    Returns:
        torch.Tensor: embeddings

    """
    return model.encode(sentences, batch_size=len(sentences))


@shared_task(name="lexy.transformers.embeddings.text_embeddings_transformer")
def text_embeddings_transformer(sentences: list[str]) -> list[dict[str, list[Tensor] | ndarray | Tensor]]:
    """ Embed sentences using SentenceTransformer.

    Args:
        sentences: list of sentences to embed

    Returns:
        torch.Tensor: embeddings

    """
    res = {'embedding': model.encode(sentences, batch_size=len(sentences))}
    return [res]


@shared_task(name="lexy.transformers.embeddings.get_chunks")
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


@shared_task(name="lexy.transformers.embeddings.just_split")
def just_split(text: str, n_times=3) -> list:
    return text.split(' ', n_times)
