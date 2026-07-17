import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch

import common
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


class InteractiveSelectTests(unittest.TestCase):
    def test_escape_exits_menu(self):
        real_select = common.questionary.select
        menu_created = Event()

        with create_pipe_input() as input_pipe:
            def select(*args, **kwargs):
                question = real_select(
                    *args, input=input_pipe, output=DummyOutput(), **kwargs
                )
                menu_created.set()
                return question

            with patch.object(common.questionary, "select", side_effect=select):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(
                        common.interactive_select,
                        "Choose:",
                        [("one", "One", 1)],
                    )
                    self.assertTrue(menu_created.wait(timeout=1))
                    input_pipe.send_text("\x1b")

                    try:
                        with self.assertRaises(SystemExit) as result:
                            future.result(timeout=1)
                    finally:
                        if not future.done():
                            input_pipe.send_text("\x03")
                            try:
                                future.result(timeout=1)
                            except BaseException:
                                pass

                    self.assertEqual(result.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
