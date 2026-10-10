import reflex as rx

import unittest
from datetime import datetime, timezone

from bson import BSON, Binary, Decimal128, ObjectId, json_util

from app.states.explorer_state import build_filter, decode_document


class BsonGuardrailTests(unittest.TestCase):
    def test_extended_json_round_trip(self):
        document = {
            "_id": ObjectId(),
            "date": datetime(2025, 1, 1, tzinfo=timezone.utc),
            "decimal": Decimal128("123.45"),
            "bytes": Binary(b"payload"),
            "nested": {"enabled": True},
            "nothing": None,
        }
        text = json_util.dumps(
            document, json_options=json_util.CANONICAL_JSON_OPTIONS
        )
        self.assertEqual(
            BSON.encode(document), BSON.encode(decode_document(text))
        )

    def test_document_must_be_object(self):
        for text in ["[]", "null", "not json", '{"_id":{"$oid":"invalid"}}']:
            with self.subTest(text=text), self.assertRaises(ValueError):
                decode_document(text)

    def test_contains_is_literal(self):
        self.assertEqual(
            build_filter("name", "contains", ".*"),
            {"name": {"$regex": "\\.\\*", "$options": "i"}},
        )

    def test_filter_preserves_typed_values(self):
        self.assertEqual(
            build_filter("count", "equals", "42"), {"count": {"$eq": 42}}
        )
        self.assertEqual(
            build_filter("name", "equals", "hello"), {"name": {"$eq": "hello"}}
        )
        identifier = ObjectId()
        self.assertEqual(
            build_filter("_id", "equals", json_util.dumps(identifier)),
            {"_id": {"$eq": identifier}},
        )

    def test_operator_injection_is_not_executed(self):
        self.assertEqual(
            build_filter("name", "equals", '{"$ne":null}'),
            {"name": {"$eq": {"$ne": None}}},
        )
        for field in ["$where", "name.$gt", "a..b", "bad\x00key"]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                build_filter(field, "equals", "1")


if __name__ == "__main__":
    unittest.main()
