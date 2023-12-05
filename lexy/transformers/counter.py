from lexy.models.document import DocumentBase
from lexy.transformers import lexy_transformer


@lexy_transformer(name="counter.count_words")
def count_words(text: str) -> dict[str, int]:
    """ Count the number of words in a text.

    Args:
        text: text to count

    Returns:
        dict[str, int]: dictionary of word counts

    Examples:
        >>> count_words("This is a test")
        {"This": 1, "is": 1, "a": 1, "test": 1}
    """
    counts = {}
    words = text.split(' ')
    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1
    return counts


@lexy_transformer(name="text.counter.word_counter")
def word_counter(text: str) -> tuple[int, str]:
    """ Testing a transformer. """
    if isinstance(text, DocumentBase):
        text = text.content
    words = text.split()
    word_count = len(words)
    longest_word = max(words, key=len)
    return word_count, longest_word
