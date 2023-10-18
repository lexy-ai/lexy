from typing import Any

from celery import shared_task


@shared_task(name="lexy.transformers.counter.count_words")
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


@shared_task(name="lexy.transformers.counter.word_counter")
def word_counter(text: str) -> list[dict[str, Any]]:
    """ Testing a transformer. """
    words = text.split()
    word_count = len(words)
    longest_word = max(words, key=len)
    return [{"word_count": word_count, "longest_word": longest_word}]

