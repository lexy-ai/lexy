from io import BytesIO

import httpx
import pypdf

from lexy.models.document import Document
from lexy.transformers import lexy_transformer
from lexy.transformers.embeddings import text_embeddings


def pdf_reader_from_url(url: str) -> pypdf.PdfReader:
    response = httpx.get(url)
    return pypdf.PdfReader(BytesIO(response.content))


@lexy_transformer(name='pdf.embed_pages.text_only')
def embed_pdf_pages(doc: Document) -> list[dict]:

    pdf = pdf_reader_from_url(doc.object_url)
    pages = []

    for page_num, page in enumerate(pdf.pages):
        page_text = page.extract_text()
        images = [im.name for im in page.images]
        p = {
            'page_text': page_text,
            'page_text_embedding': text_embeddings(page_text),
            'page_meta': {
                'page_num': page_num,
                'page_text_length': len(page_text),
                'images': images,
                'n_images': len(images)
            }
        }
        pages.append(p)

    return pages
