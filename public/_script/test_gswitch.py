import unittest

import gswitch


class BranchMenuTests(unittest.TestCase):
    def test_shows_local_and_remote_entries_with_the_same_name(self):
        self.assertEqual(
            gswitch.build_branch_items(
                "main",
                ["feature/a", "main"],
                ["origin/feature/a", "origin/release"],
            ),
            [
                ("main", "* [本地] main", "local\tmain"),
                ("feature/a", "  [本地] feature/a", "local\tfeature/a"),
                (
                    "origin/feature/a",
                    "  [远端] origin/feature/a",
                    "remote\torigin/feature/a",
                ),
                ("origin/release", "  [远端] origin/release", "remote\torigin/release"),
            ],
        )

    def test_hides_remote_head_reference(self):
        self.assertEqual(
            gswitch.build_branch_items("", [], ["origin/HEAD", "origin/main"]),
            [("origin/main", "  [远端] origin/main", "remote\torigin/main")],
        )


if __name__ == "__main__":
    unittest.main()
