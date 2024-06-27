import json

from lexy_py.filters import FilterBuilder


class TestFilterBuilder:
    def test_filter_builder(self):
        builder = FilterBuilder()
        builder.include("content", "contains_ci", "mathematics")
        assert builder.to_json() == (
            '{"conditions": [{"field": "content", "operation": "contains_ci", "value": '
            '"mathematics", "negate": false}], "combination": "AND"}'
        )
        builder.include("meta.size", "less_than", 30000).exclude(
            "meta.type", "in", ["image", "video"]
        )
        assert builder.to_json() == (
            '{"conditions": [{"field": "content", "operation": "contains_ci", "value": '
            '"mathematics", "negate": false}, {"field": "meta.size", "operation": '
            '"less_than", "value": 30000, "negate": false}, {"field": "meta.type", '
            '"operation": "in", "value": ["image", "video"], "negate": true}], '
            '"combination": "AND"}'
        )
        assert builder.to_dict() == {
            "conditions": [
                {
                    "field": "content",
                    "operation": "contains_ci",
                    "value": "mathematics",
                    "negate": False,
                },
                {
                    "field": "meta.size",
                    "operation": "less_than",
                    "value": 30000,
                    "negate": False,
                },
                {
                    "field": "meta.type",
                    "operation": "in",
                    "value": ["image", "video"],
                    "negate": True,
                },
            ],
            "combination": "AND",
        }
        assert builder.to_dict() == json.loads(builder.to_json())

        builder = FilterBuilder()
        builder.exclude("meta.url", "starts_with", "https://www.youtube.com").exclude(
            "meta.url", "equals", None
        )
        assert builder.to_json() == (
            '{"conditions": [{"field": "meta.url", "operation": "starts_with", "value": '
            '"https://www.youtube.com", "negate": true}, {"field": "meta.url", '
            '"operation": "equals", "value": null, "negate": true}], "combination": "AND"}'
        )
        assert builder.to_dict() == {
            "conditions": [
                {
                    "field": "meta.url",
                    "operation": "starts_with",
                    "value": "https://www.youtube.com",
                    "negate": True,
                },
                {
                    "field": "meta.url",
                    "operation": "equals",
                    "value": None,
                    "negate": True,
                },
            ],
            "combination": "AND",
        }
        assert builder.to_dict() == json.loads(builder.to_json())
