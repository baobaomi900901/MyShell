import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config_entries
import cd
import pw
import vscode


class ConfigEntryOrderTests(unittest.TestCase):
    def test_order_handles_missing_duplicate_and_invalid_indexes(self):
        data = {
            "later": {"index": 20},
            "unindexed": {},
            "beta": {"index": 2},
            "alpha": {"index": 2},
            "invalid": {"index": "1"},
            "first": {"index": 0},
        }
        self.assertEqual(
            config_entries.sorted_config_keys(data),
            ["first", "alpha", "beta", "later", "invalid", "unindexed"],
        )
        self.assertEqual(config_entries.sorted_config_keys(data, {"beta", "unindexed"}), ["beta", "unindexed"])

    def test_completion_uses_same_order_without_exposing_passwords(self):
        data = {
            "last_item": {"password": "secret-last", "description": "last"},
            "first_item": {"password": "secret-first", "description": "first", "index": 1},
        }
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "password.json"
            config.write_text(json.dumps(data), encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(config_entries.main([str(config), "password", "json"]), 0)
        self.assertEqual([row["name"] for row in json.loads(output.getvalue())], ["first_item", "last_item"])
        self.assertNotIn("secret-", output.getvalue())

    def test_all_three_interactive_menus_use_index_order(self):
        with tempfile.TemporaryDirectory() as directory:
            data = {
                "last": {"mac": directory, "password": "last-secret"},
                "first": {"mac": directory, "password": "first-secret", "index": 1},
            }
            for module in (cd, vscode, pw):
                selected = []

                def capture(_title, items, **_kwargs):
                    selected.extend(key for key, _display, _value in items)
                    return None, None

                with mock.patch.object(module, "load_json_config", return_value=data), mock.patch.object(
                    module, "interactive_select", side_effect=capture
                ), mock.patch.object(module.sys, "argv", ["script", "config", "output"]):
                    if module is not pw:
                        with mock.patch.object(module, "get_system_type", return_value="mac"):
                            with self.assertRaises(SystemExit):
                                module.main()
                    else:
                        with self.assertRaises(SystemExit):
                            module.main()
                self.assertEqual(selected, ["first", "last"])


if __name__ == "__main__":
    unittest.main()
