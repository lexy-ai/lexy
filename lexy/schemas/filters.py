from enum import Enum
from typing import Any, Iterable

from pydantic import BaseModel, Field, validator

from lexy.models.document import Document


class Operation(str, Enum):
    EQUALS = 'equals'
    EQUALS_CI = 'equals_ci'  # Case-insensitive equals
    NOT_EQUALS = 'not_equals'
    LESS_THAN = 'less_than'
    LESS_THAN_OR_EQUALS = 'less_than_or_equals'
    GREATER_THAN = 'greater_than'
    GREATER_THAN_OR_EQUALS = 'greater_than_or_equals'
    CONTAINS = 'contains'
    CONTAINS_CI = 'contains_ci'  # Case-insensitive contains
    NOT_CONTAINS = 'not_contains'
    NOT_CONTAINS_CI = 'not_contains_ci'  # Case-insensitive not contains
    STARTS_WITH = 'starts_with'
    STARTS_WITH_CI = 'starts_with_ci'  # Case-insensitive starts with
    ENDS_WITH = 'ends_with'
    ENDS_WITH_CI = 'ends_with_ci'  # Case-insensitive ends with
    IN = 'in'
    NOT_IN = 'not_in'


class FilterCriterion(BaseModel):
    field: str = Field(..., description="The field to apply the filter on")
    operation: Operation = Field(..., description="The operation to perform")
    value: Any = Field(..., description="The value to compare against")
    negate: bool = Field(False, description="Whether to negate the filter criterion")

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
        if operation in [Operation.IN,
                         Operation.NOT_IN]:
            if not isinstance(v, Iterable):
                raise ValueError(
                    f"Value must be an iterable (list, tuple, set, or dict) for operation {operation}")

        # For string operations
        if operation in [Operation.EQUALS_CI,
                         Operation.CONTAINS,
                         Operation.CONTAINS_CI,
                         Operation.NOT_CONTAINS,
                         Operation.NOT_CONTAINS_CI,
                         Operation.STARTS_WITH,
                         Operation.STARTS_WITH_CI,
                         Operation.ENDS_WITH,
                         Operation.ENDS_WITH_CI]:
            if not isinstance(v, str):
                raise ValueError(f"Value must be a string for operation {operation}")

        return v


class Filter(BaseModel):
    filters: list[FilterCriterion]
    combination: str = Field(..., description="Logical combination (AND/OR)")

    def document_meets_criteria(self, document: Document) -> bool:
        if self.combination == "AND":
            return all(apply_filter_criterion(document, criterion) for criterion in self.filters)
        elif self.combination == "OR":
            return any(apply_filter_criterion(document, criterion) for criterion in self.filters)
        else:
            raise ValueError(f"Unsupported combination: {self.combination}")


# Function to apply individual filter criterion to a document
def apply_filter_criterion(document: Document, criterion: FilterCriterion) -> bool:
    if criterion.field.startswith('meta.'):
        doc_value = document.meta.get(criterion.field[5:], None)
    else:
        doc_value = getattr(document, criterion.field, None)
    filter_value = criterion.value

    # handle case where doc value is None
    if doc_value is None:
        if criterion.operation in [Operation.EQUALS,
                                   Operation.EQUALS_CI]:
            return filter_value is None
        elif criterion.operation == Operation.NOT_EQUALS:
            return filter_value is not None
        elif criterion.operation in [Operation.LESS_THAN,
                                     Operation.LESS_THAN_OR_EQUALS,
                                     Operation.GREATER_THAN,
                                     Operation.GREATER_THAN_OR_EQUALS]:
            return False
        elif criterion.operation in [Operation.CONTAINS,
                                     Operation.CONTAINS_CI,
                                     Operation.NOT_CONTAINS,
                                     Operation.NOT_CONTAINS_CI,
                                     Operation.STARTS_WITH,
                                     Operation.STARTS_WITH_CI,
                                     Operation.ENDS_WITH,
                                     Operation.ENDS_WITH_CI]:
            return False
        elif criterion.operation in [Operation.IN,
                                     Operation.NOT_IN]:
            return None in filter_value if isinstance(filter_value, Iterable) else False
        else:
            raise ValueError(f"Unsupported operation: {criterion.operation} for doc value `None`")

    if criterion.operation == Operation.EQUALS:
        return doc_value == filter_value
    elif criterion.operation == Operation.EQUALS_CI:
        return str(doc_value).lower() == str(filter_value).lower()
    elif criterion.operation == Operation.NOT_EQUALS:
        return doc_value != filter_value
    elif criterion.operation == Operation.LESS_THAN:
        return doc_value < filter_value
    elif criterion.operation == Operation.LESS_THAN_OR_EQUALS:
        return doc_value <= filter_value
    elif criterion.operation == Operation.GREATER_THAN:
        return doc_value > filter_value
    elif criterion.operation == Operation.GREATER_THAN_OR_EQUALS:
        return doc_value >= filter_value
    elif criterion.operation == Operation.CONTAINS:
        return filter_value in doc_value
    elif criterion.operation == Operation.CONTAINS_CI:
        return str(filter_value).lower() in str(doc_value).lower()
    elif criterion.operation == Operation.NOT_CONTAINS:
        return filter_value not in doc_value
    elif criterion.operation == Operation.NOT_CONTAINS_CI:
        return str(filter_value).lower() not in str(doc_value).lower()
    elif criterion.operation == Operation.STARTS_WITH:
        return doc_value.startswith(filter_value)
    elif criterion.operation == Operation.STARTS_WITH_CI:
        return str(doc_value).lower().startswith(str(filter_value).lower())
    elif criterion.operation == Operation.ENDS_WITH:
        return doc_value.endswith(filter_value)
    elif criterion.operation == Operation.ENDS_WITH_CI:
        return str(doc_value).lower().endswith(str(filter_value).lower())
    elif criterion.operation == Operation.IN:
        return doc_value in filter_value
    elif criterion.operation == Operation.NOT_IN:
        return doc_value not in filter_value
    else:
        raise ValueError(f"Unsupported operation: {criterion.operation}")


# Function to apply all filters to a list of documents
def filter_documents(docs: Iterable[Document], filter_obj: Filter) -> Iterable[Document]:
    """Filter documents according to a filter object.

    Args:
        docs (Iterable[Document]): The documents to filter.
        filter_obj (Filter): The filter object to apply.

    Yields:
        Iterable[Document]: The filtered documents.

    Examples:
        >>> filter_obj = Filter(filters=[FilterCriterion(field='text', operation='contains', value='foo'),
        ...                              FilterCriterion(field='meta.bar', operation='equals', value='baz')],
        ...                     combination='AND')
        >>> docs = [Document(content='foo bar', meta={'bar': 'baz'}), Document(content='foo', meta={'bar': 'qux'})]
        >>> list(filter_documents(docs, filter_obj))
        [Document(content='foo bar', meta={'bar': 'baz'})]
    """
    for doc in docs:
        if filter_obj.combination == 'AND':
            if all(apply_filter_criterion(doc, criterion) for criterion in filter_obj.filters):
                yield doc
        elif filter_obj.combination == 'OR':
            if any(apply_filter_criterion(doc, criterion) for criterion in filter_obj.filters):
                yield doc
        else:
            raise ValueError(f"Unsupported combination: {filter_obj.combination}")


def document_passes_filter(document: Document, filter_obj: Filter) -> bool:
    if filter_obj.combination == "AND":
        return all(apply_filter_criterion(document, criterion) for criterion in filter_obj.filters)
    elif filter_obj.combination == "OR":
        return any(apply_filter_criterion(document, criterion) for criterion in filter_obj.filters)
    else:
        raise ValueError(f"Unsupported combination: {filter_obj.combination}")
