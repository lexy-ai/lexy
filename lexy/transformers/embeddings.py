from celery import shared_task

import torch
from sentence_transformers import SentenceTransformer

from lexy.models.document import Document


torch.set_num_threads(1)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_default_transformer():
    return """
import torch
from sentence_transformers import SentenceTransformer
torch.set_num_threads(1)
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                       
def transform(document):
    return model.encode([document.content], batch_size=len([document.content]))
"""

@shared_task(name="custom_transformer")
def custom_transformer(document: Document, transformer: str) -> list[dict]:
    """ Apply a custom transformer to a document.
    
    Args:
        document: document to transform
        
    Returns:
        list[dict]: list of results"""
    
    __return__ = []
    transformer_with_return = f"""
{transformer}

__return__ = transform(document)"""
    vars = {"document": document}
    exec(transformer_with_return, None, vars)
    return vars['__return__']


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
