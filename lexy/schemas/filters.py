from enum import Enum
from typing import Any, Iterable, TYPE_CHECKING

from pydantic import BaseModel, Field, validator

if TYPE_CHECKING:
    from lexy.models.document import Document


class Operation(str, Enum):
    EQUALS = 'equals'
    EQUALS_CI = 'equals_ci'  # Case-insensitive equals
    LESS_THAN = 'less_than'
    LESS_THAN_OR_EQUALS = 'less_than_or_equals'
    GREATER_THAN = 'greater_than'
    GREATER_THAN_OR_EQUALS = 'greater_than_or_equals'
    CONTAINS = 'contains'
    CONTAINS_CI = 'contains_ci'  # Case-insensitive contains
    STARTS_WITH = 'starts_with'
    STARTS_WITH_CI = 'starts_with_ci'  # Case-insensitive starts with
    ENDS_WITH = 'ends_with'
    ENDS_WITH_CI = 'ends_with_ci'  # Case-insensitive ends with
    IN = 'in'


class FilterCondition(BaseModel):
    field: str = Field(..., description="The field to apply the filter on")
    operation: str = Field(..., description="The operation to perform")
    value: Any = Field(..., description="The value to compare against")
    negate: bool = Field(False, description="Whether to negate the filter condition")

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator('value', pre=True)
    def validate_value(cls, v, values, **kwargs):
        operation = values.get('operation')

        # For numeric operations
        if operation in [Operation.LESS_THAN,
                         Operation.LESS_THAN_OR_EQUALS,
                         Operation.GREATER_THAN,
                         Operation.GREATER_THAN_OR_EQUALS]:
            try:
                return float(v)
            except ValueError:
                raise ValueError(f"Value must be a number for operation {operation}")

        # For iterable operations
        if operation in [Operation.IN]:
            if not isinstance(v, Iterable):
                raise ValueError(
                    f"Value must be an iterable (list, tuple, set, or dict) for operation {operation}")

        # For string operations
        if operation in [Operation.EQUALS_CI,
                         Operation.CONTAINS,
                         Operation.CONTAINS_CI,
                         Operation.STARTS_WITH,
                         Operation.STARTS_WITH_CI,
                         Operation.ENDS_WITH,
                         Operation.ENDS_WITH_CI]:
            if not isinstance(v, str):
                raise ValueError(f"Value must be a string for operation {operation}")

        return v


class Filter(BaseModel):
    conditions: list[FilterCondition]
    combination: str = Field("AND", description="Logical combination (AND/OR)")

    def document_meets_conditions(self, document: "Document") -> bool:
        if self.combination == "AND":
            return all(apply_filter_condition(document, condition) for condition in self.conditions)
        elif self.combination == "OR":
            return any(apply_filter_condition(document, condition) for condition in self.conditions)
        else:
            raise ValueError(f"Unsupported combination: {self.combination}")


# Function to apply individual filter condition to a document
def apply_filter_condition(document: "Document", condition: FilterCondition) -> bool:
    if condition.field.startswith('meta.'):
        doc_value = document.meta.get(condition.field[5:], None)
    else:
        doc_value = getattr(document, condition.field, None)
    filter_value = condition.value

    if doc_value is None:
        # handle case where doc value is None
        if condition.operation in [Operation.EQUALS,
                                   Operation.EQUALS_CI]:
            result = filter_value is None
        elif condition.operation in [Operation.LESS_THAN,
                                     Operation.LESS_THAN_OR_EQUALS,
                                     Operation.GREATER_THAN,
                                     Operation.GREATER_THAN_OR_EQUALS,
                                     Operation.CONTAINS,
                                     Operation.CONTAINS_CI,
                                     Operation.STARTS_WITH,
                                     Operation.STARTS_WITH_CI,
                                     Operation.ENDS_WITH,
                                     Operation.ENDS_WITH_CI]:
            result = False
        elif condition.operation in [Operation.IN]:
            result = None in filter_value if isinstance(filter_value, Iterable) else False
        else:
            raise ValueError(f"Unsupported operation: {condition.operation} for doc value `None`")
    else:
        # handle all other cases
        if condition.operation == Operation.EQUALS:
            result = doc_value == filter_value
        elif condition.operation == Operation.EQUALS_CI:
            result = str(doc_value).lower() == str(filter_value).lower()
        elif condition.operation == Operation.LESS_THAN:
            result = doc_value < filter_value
        elif condition.operation == Operation.LESS_THAN_OR_EQUALS:
            result = doc_value <= filter_value
        elif condition.operation == Operation.GREATER_THAN:
            result = doc_value > filter_value
        elif condition.operation == Operation.GREATER_THAN_OR_EQUALS:
            result = doc_value >= filter_value
        elif condition.operation == Operation.CONTAINS:
            result = filter_value in doc_value
        elif condition.operation == Operation.CONTAINS_CI:
            result = str(filter_value).lower() in str(doc_value).lower()
        elif condition.operation == Operation.STARTS_WITH:
            result = doc_value.startswith(filter_value)
        elif condition.operation == Operation.STARTS_WITH_CI:
            result = str(doc_value).lower().startswith(str(filter_value).lower())
        elif condition.operation == Operation.ENDS_WITH:
            result = doc_value.endswith(filter_value)
        elif condition.operation == Operation.ENDS_WITH_CI:
            result = str(doc_value).lower().endswith(str(filter_value).lower())
        elif condition.operation == Operation.IN:
            result = doc_value in filter_value
        else:
            raise ValueError(f"Unsupported operation: {condition.operation}")

    return not result if condition.negate else result


# Function to apply all filters to a list of documents
def filter_documents(docs: Iterable["Document"], filter_obj: Filter) -> Iterable["Document"]:
    """Filter documents according to a filter object.

    Args:
        docs (Iterable[Document]): The documents to filter.
        filter_obj (Filter): The filter object to apply.

    Yields:
        Iterable[Document]: The filtered documents.

    Examples:
        >>> filter_obj = Filter(conditions=[FilterCondition(field='text', operation='contains', value='foo'),
        ...                                 FilterCondition(field='meta.bar', operation='equals', value='baz')],
        ...                     combination='AND')
        >>> docs = [Document(content='foo bar', meta={'bar': 'baz'}), Document(content='foo', meta={'bar': 'qux'})]
        >>> list(filter_documents(docs, filter_obj))
        [Document(content='foo bar', meta={'bar': 'baz'})]
    """
    for doc in docs:
        if filter_obj.combination == 'AND':
            if all(apply_filter_condition(doc, condition) for condition in filter_obj.conditions):
                yield doc
        elif filter_obj.combination == 'OR':
            if any(apply_filter_condition(doc, condition) for condition in filter_obj.conditions):
                yield doc
        else:
            raise ValueError(f"Unsupported combination: {filter_obj.combination}")


def document_passes_filter(document: "Document", filter_obj: Filter) -> bool:
    if filter_obj.combination == "AND":
        return all(apply_filter_condition(document, condition) for condition in filter_obj.conditions)
    elif filter_obj.combination == "OR":
        return any(apply_filter_condition(document, condition) for condition in filter_obj.conditions)
    else:
        raise ValueError(f"Unsupported combination: {filter_obj.combination}")
