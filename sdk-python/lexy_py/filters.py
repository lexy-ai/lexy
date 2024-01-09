import json
from typing import Any


class FilterBuilder:
    """Helper class for creating filters.

    Attributes:
        conditions (list[dict]): A list of conditions to be combined. Each condition consists of a field, an operation,
            and a value. The field is a string representing the field to be matched. The operation is a string representing the
            operation to be performed on the field. The value is the value to be matched against.

            Valid operations include the following.

            - `equals`
            - `equals_ci` (case-insensitive equals)
            - `less_than`
            - `less_than_or_equals`
            - `greater_than`
            - `greater_than_or_equals`
            - `in`
            - `contains`
            - `contains_ci` (case-insensitive contains)
            - `starts_with`
            - `starts_with_ci` (case-insensitive starts_with)
            - `ends_with`
            - `ends_with_ci` (case-insensitive ends_with)
        combination (str): The combination of conditions - either 'AND' or 'OR'

    Methods:
        include: Adds a condition to the filter object with a positive match
        exclude: Adds a condition to the filter object with a negative match
        to_dict: Returns the filter object as a dictionary
        to_json: Returns the filter object as a JSON string

    Examples:
        Restrict documents to those that contain the word 'mathematics' regardless of the case:

        >>> from lexy_py import FilterBuilder
        >>> builder = FilterBuilder()
        >>> builder.include("content", "contains_ci", "mathematics")
        >>> print(builder.to_json())
        {
            "conditions": [
                {"field": "content", "operation": "contains_ci", "value": "mathematics", "negate": false}
            ],
            "combination": "AND"
        }

        Restrict documents to those with a size less than 30,000 bytes and a file type that is not an image or video:

        >>> builder = FilterBuilder()
        >>> builder.include("meta.size", "less_than", 30000)
        >>> builder.exclude("meta.type", "in", ["image", "video"])
        >>> print(builder.to_json())
        {
            "conditions": [
                {"field": "meta.size", "operation": "less_than", "value": 30000, "negate": false},
                {"field": "meta.type", "operation": "in", "value": ["image", "video"], "negate": true}
            ],
            "combination": "AND"
        }

        Restrict documents to those where URL is not None and does not start with 'https://www.youtube.com':

        >>> builder = FilterBuilder()
        >>> builder.exclude("meta.url", "starts_with", "https://www.youtube.com")
        >>> builder.exclude("meta.url", "equals", None)
        >>> builder.to_dict()
        {
            "conditions": [
                {"field": "meta.url", "operation": "starts_with", "value": "https://www.youtube.com", "negate": True},
                {"field": "meta.url", "operation": "equals", "value": None, "negate": True}
            ],
            "combination": "AND"
        }
    """

    def __init__(self, conditions: list[dict] = None, combination: str = "AND"):
        self.conditions = conditions or []
        if combination.upper() not in ["AND", "OR"]:
            raise ValueError("Invalid combination - must be 'AND' or 'OR'")
        self.combination = combination.upper()

    def include(self, field: str, operation: str, value: Any):
        """Adds a condition to the filter object with a positive match

        Args:
            field: The field to be matched
            operation: The operation to be performed on the field. Must be one of the following.

                - `equals`
                - `equals_ci` (case-insensitive equals)
                - `less_than`
                - `less_than_or_equals`
                - `greater_than`
                - `greater_than_or_equals`
                - `in`
                - `contains`
                - `contains_ci` (case-insensitive contains)
                - `starts_with`
                - `starts_with_ci` (case-insensitive starts_with)
                - `ends_with`
                - `ends_with_ci` (case-insensitive ends_with)
            value: The value to be matched against
        """
        self.conditions.append({
            "field": field,
            "operation": operation,
            "value": value,
            "negate": False
        })
        return self

    def exclude(self, field: str, operation: str, value: Any):
        """Adds a condition to the filter object with a negative match

        Args:
            field: The field to be matched
            operation: The operation to be performed on the field. Must be one of the following.

                - `equals`
                - `equals_ci` (case-insensitive equals)
                - `less_than`
                - `less_than_or_equals`
                - `greater_than`
                - `greater_than_or_equals`
                - `in`
                - `contains`
                - `contains_ci` (case-insensitive contains)
                - `starts_with`
                - `starts_with_ci` (case-insensitive starts_with)
                - `ends_with`
                - `ends_with_ci` (case-insensitive ends_with)
            value: The value to be matched against
        """
        self.conditions.append({
            "field": field,
            "operation": operation,
            "value": value,
            "negate": True
        })
        return self

    def to_dict(self) -> dict:
        return {
            "conditions": self.conditions,
            "combination": self.combination
        }

    def to_json(self) -> str:
        return json.dumps({
            "conditions": self.conditions,
            "combination": self.combination
        })
