import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

# Seed minimal DB config before importing loader module.
os.environ.setdefault("DB_USER", "tester")
os.environ.setdefault("DB_PASSWORD", "secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "kyagent_test")

from app.database.load_data import find_existing_program, update_program_from_data


class SequencedQuery:
    def __init__(self, first_results):
        self._results = list(first_results)
        self._index = 0

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        result = self._results[self._index]
        self._index += 1
        return result


class LoadDataHelperTests(unittest.TestCase):
    def test_update_program_from_data_sets_all_fields(self):
        program = SimpleNamespace(total_score=320, notes="old", discipline_category="工学")

        update_program_from_data(program, {
            "total_score": 350,
            "notes": "updated",
            "discipline_category": "理学",
        })

        self.assertEqual(program.total_score, 350)
        self.assertEqual(program.notes, "updated")
        self.assertEqual(program.discipline_category, "理学")

    def test_find_existing_program_prefers_program_code_match(self):
        expected = object()
        session = MagicMock()
        session.query.return_value = SequencedQuery([expected])

        found = find_existing_program(session, 1, {
            "year": 2024,
            "program_code": "081200",
            "program_name": "计算机科学与技术",
            "program_type": "学术型硕士",
        })

        self.assertIs(found, expected)

    def test_find_existing_program_falls_back_to_name_and_type(self):
        expected = object()
        session = MagicMock()
        session.query.return_value = SequencedQuery([expected])

        found = find_existing_program(session, 1, {
            "year": 2024,
            "program_code": "",
            "program_name": "计算机技术",
            "program_type": "专业型硕士",
        })

        self.assertIs(found, expected)

    def test_find_existing_program_returns_none_without_school_or_year(self):
        session = MagicMock()

        self.assertIsNone(find_existing_program(session, None, {"year": 2024}))
        self.assertIsNone(find_existing_program(session, 1, {}))
        session.query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
