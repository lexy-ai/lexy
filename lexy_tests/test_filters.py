from lexy.models import Document
from lexy.schemas.filters import Filter, FilterCondition, filter_documents, Operation


documents = [
    Document(content='', meta={'size': 10000, 'type': 'image', 'category': 'photo'}),
    Document(content='this is my text content'),
    Document(content='', meta={'size': 50000, 'type': 'video', 'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}),
    Document(content='', meta={'size': 12345, 'type': 'pdf', 'url': 'https://www.reddit.com/reddit.pdf'}),
]


class TestFilters:

    def test_hello(self):
        assert True

    def test_filter_documents(self):
        filter_obj = Filter(
            conditions=[
                FilterCondition(
                    field="content",
                    operation=Operation.CONTAINS,
                    value="text"
                )
            ]
        )
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 1
        assert filtered_docs[0].content == "this is my text content"

    def test_filter_documents_with_multiple_conditions(self):
        filter_obj = Filter(
            conditions=[
                FilterCondition(
                    field="content",
                    operation=Operation.CONTAINS,
                    value="text"
                ),
                FilterCondition(
                    field="meta.size",
                    operation=Operation.GREATER_THAN,
                    value=10000
                )
            ]
        )
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 0

    def test_filter_documents_with_in_condition(self):
        filter_obj = Filter.parse_obj({
            "conditions": [
                {"field": "meta.size", "operation": "less_than", "value": 30000},
                {"field": "meta.type", "operation": "in", "value": ["image", "video"]}
            ],
            "combination": "AND"
        })
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 1
        assert filtered_docs[0] == documents[0]

    def test_filter_documents_with_exclude_in_condition(self):
        filter_obj = Filter.parse_obj({
            "conditions": [
                {"field": "meta.size", "operation": "less_than", "value": 30000},
                {"field": "meta.type", "operation": "in", "value": ["image", "video"], "negate": True}
            ],
            "combination": "AND"
        })
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 1
        assert filtered_docs[0] == documents[3]

    def test_filter_documents_with_isnull_condition(self):
        filter_obj = Filter.parse_obj({
            "conditions": [
                {"field": "meta.size", "operation": "equals", "value": None}
            ],
            "combination": "AND"
        })
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 1
        assert filtered_docs[0] == documents[1]

    def test_filter_documents_with_notnull_condition(self):
        filter_obj = Filter.parse_obj({
            "conditions": [
                {"field": "meta.size", "operation": "equals", "value": None, "negate": True}
            ],
            "combination": "AND"
        })
        filtered_docs = list(filter_documents(documents, filter_obj))
        assert len(filtered_docs) == 3
        assert filtered_docs[0] == documents[0]
        assert filtered_docs[1] == documents[2]
        assert filtered_docs[2] == documents[3]
