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
