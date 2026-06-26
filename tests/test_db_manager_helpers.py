import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

# Seed minimal DB config before importing models-backed modules.
os.environ.setdefault("DB_USER", "tester")
os.environ.setdefault("DB_PASSWORD", "secret")
os.environ.setdefault("DB_HOST", "localhost")
os.environ.setdefault("DB_PORT", "3306")
os.environ.setdefault("DB_NAME", "kyagent_test")

from app.database.db_manager import DatabaseManager


class DatabaseManagerHelperTests(unittest.TestCase):
    def test_get_auth_credentials_builds_expected_mapping(self):
        manager = DatabaseManager.__new__(DatabaseManager)
        manager.get_all_users = MagicMock(return_value=[
            SimpleNamespace(username="alice", name="Alice", password="hash-a"),
            SimpleNamespace(username="bob", name="Bob", password="hash-b"),
        ])

        credentials = DatabaseManager.get_auth_credentials(manager)

        self.assertEqual(
            credentials,
            {
                "usernames": {
                    "alice": {"name": "Alice", "password": "hash-a"},
                    "bob": {"name": "Bob", "password": "hash-b"},
                }
            },
        )

    def test_get_school_stats_data_shapes_home_page_fields(self):
        manager = DatabaseManager.__new__(DatabaseManager)
        manager.get_all_schools = MagicMock(return_value=[
            SimpleNamespace(name="Alpha University", province="北京", type="985", master_programs=12, doctoral_programs=8),
            SimpleNamespace(name="Beta University", province="上海", type="211", master_programs=9, doctoral_programs=4),
        ])

        df = DatabaseManager.get_school_stats_data(manager)

        self.assertEqual(list(df.columns), ["name", "province", "type", "master_programs", "doctoral_programs"])
        self.assertEqual(df.to_dict("records")[0]["name"], "Alpha University")
        self.assertEqual(df.to_dict("records")[1]["doctoral_programs"], 4)

    def test_get_school_names_returns_name_list(self):
        manager = DatabaseManager.__new__(DatabaseManager)
        manager.get_all_schools = MagicMock(return_value=[
            SimpleNamespace(name="Alpha University"),
            SimpleNamespace(name="Beta University"),
        ])

        names = DatabaseManager.get_school_names(manager)

        self.assertEqual(names, ["Alpha University", "Beta University"])

    def test_get_discipline_counts_returns_dataframe_from_aggregated_rows(self):
        manager = DatabaseManager.__new__(DatabaseManager)
        manager.session = MagicMock()
        query = manager.session.query.return_value
        query.filter.return_value = query
        query.group_by.return_value = query
        query.order_by.return_value = query
        query.all.return_value = [("工学", 3), ("理学", 2)]

        df = DatabaseManager.get_discipline_counts(manager)

        self.assertEqual(df.to_dict("records"), [
            {"discipline": "工学", "count": 3},
            {"discipline": "理学", "count": 2},
        ])


if __name__ == "__main__":
    unittest.main()
