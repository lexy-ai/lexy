from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer

import torch
from PIL.Image import Image
from transformers import CLIPProcessor, CLIPModel

torch.set_num_threads(1)
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# move model to device if possible
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model.to(device)


@lexy_transformer(name="image.embeddings.clip")
def image_embeddings_clip(images: Image | list[Image]) -> torch.Tensor:
    """Embed images using CLIP.

    Args:
        images: A single image or a list of images to embed.

    Returns:
        torch.Tensor: The embeddings of the provided images.
    """

    image_batch = processor(
        text=None,
        images=images,
        return_tensors='pt'
    )['pixel_values'].to(device)

    if isinstance(images, list):
        return model.get_image_features(image_batch)
    else:
        return model.get_image_features(image_batch)[0]


@lexy_transformer(name="text.embeddings.clip")
def text_embeddings_clip(text: list[str | DocumentBase] | str | DocumentBase) -> torch.Tensor:
    """Embed text using CLIP.

    Args:
        text: A single string or DocumentBase instance, or a list of strings or DocumentBase instances to embed.

    Returns:
        torch.Tensor: The embeddings of the provided text.
    """
    if isinstance(text, DocumentBase):
        text = text.content
    elif isinstance(text, list):
        text = [s.content if isinstance(s, DocumentBase) else s for s in text]
    tokens = processor(
        text=text,
        padding=True,
        images=None,
        return_tensors='pt'
    ).to(device)
    text_emb = model.get_text_features(
        **tokens
    )
    if isinstance(text, list):
        return text_emb
    else:
        return text_emb[0]
