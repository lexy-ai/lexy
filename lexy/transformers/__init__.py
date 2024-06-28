import functools

from celery import shared_task


def lexy_fields(func):
    """A decorator to assign index field labels to a transformer's return values.

    Args:
        func: The transformer function to decorate

    Returns:
        function: The decorated transformer function

    Examples:
        >>> @lexy_fields
        ... def add_and_subtract(a, b):
        ...     return a + b, a - b
        ...
        >>> add_and_subtract(5, 3, lexy_fields=["sum", "difference"])
        {'sum': 8, 'difference': 2}
        >>> add_and_subtract(5, 3, lexy_fields=["addition", "subtraction"])
        {'addition': 8, 'subtraction': 2}
        >>> add_and_subtract(5, 3)
        (8, 2)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        fields = kwargs.pop("lexy_fields", [])
        results = func(*args, **kwargs)

        # if no lexy fields are provided, return the original results
        if not fields:
            return results

        # if the function returns a single value, wrap it in a tuple
        if not isinstance(results, tuple):
            results = (results,)

        # check if the number of lexy fields matches the number of results
        if len(fields) != len(results):
            raise ValueError(
                f"Expected {len(fields)} lexy fields ({', '.join(fields)}), "
                f"but got {len(results)} return values from '{func.__name__}'."
            )

        # zip together labels and results and return as a dictionary inside a list
        return [dict(zip(fields, results))]

    # modify the docstring to include documentation for the "lexy_fields" parameter
    lexy_doc = (
        "\n\n"
        "Lexy Transformer options:\n\n"
        "\tlexy_fields: list, optional\n"
        "\t    A list of field names to be used for the return values.\n"
    )
    if func.__doc__:
        wrapper.__doc__ = func.__doc__ + lexy_doc
    else:
        wrapper.__doc__ = lexy_doc

    return wrapper


def lexy_transformer(name: str, **task_kwargs):
    """A decorator to register a transformer function with Lexy.

    Args:
        name: The name of the transformer. The task will be registered with Celery as "lexy.transformers.{name}"
        **task_kwargs: Keyword arguments to pass to the Celery task decorator
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lexy_index_fields = kwargs.pop("lexy_index_fields", [])
            results = func(*args, **kwargs)

            # if no index fields are provided, return the original results
            if not lexy_index_fields:
                return results

            # if the function returns a single value, wrap it in a tuple
            if not isinstance(results, tuple):
                results = (results,)

            # check if the number of index fields matches the number of results
            if len(lexy_index_fields) != len(results):
                raise ValueError(
                    f"Expected {len(lexy_index_fields)} index fields ({', '.join(lexy_index_fields)}), "
                    f"but got {len(results)} return values from '{func.__name__}'."
                )

            # zip together labels and results and return as a dictionary inside a list
            return [dict(zip(lexy_index_fields, results))]

        # modify the docstring to include documentation for the "lexy_index_fields" parameter
        lexy_doc = (
            "\n\n"
            "Lexy Transformer options:\n\n"
            "\tlexy_index_fields: list, optional\n"
            "\t    A list of index fields to be used for the return values.\n"
        )
        if func.__doc__:
            wrapper.__doc__ = func.__doc__ + lexy_doc
        else:
            wrapper.__doc__ = lexy_doc

        wrapper = shared_task(name=f"lexy.transformers.{name}", **task_kwargs)(wrapper)
        return wrapper

    return decorator
