from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer

import torch
from sentence_transformers import SentenceTransformer


torch.set_num_threads(1)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


@lexy_transformer(name="text.embeddings.minilm")
def text_embeddings(
    sentences: list[str | DocumentBase] | str | DocumentBase,
) -> torch.Tensor:
    """Embed sentences using SentenceTransformer.

    Args:
        sentences: A single sentence or a list of sentences to embed. Each sentence can
            be either a string or a DocumentBase instance.

    Returns:
        torch.Tensor: The embeddings of the provided sentences.
    """
    if isinstance(sentences, DocumentBase):
        sentences = sentences.content
    elif isinstance(sentences, list):
        sentences = [s.content if isinstance(s, DocumentBase) else s for s in sentences]
    return model.encode(sentences, batch_size=len(sentences))
