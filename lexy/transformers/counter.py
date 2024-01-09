from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer


@lexy_transformer(name="text.counter.word_counter")
def word_counter(text: str) -> tuple[int, str]:
    """ Testing a transformer. """
    if isinstance(text, DocumentBase):
        text = text.content
    words = text.split()
    word_count = len(words)
    longest_word = max(words, key=len)
    return word_count, longest_word
