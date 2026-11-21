import contextlib
import io
import unittest
from unittest.mock import patch


def run_main(mac_models):
    try:
        mac_models.main()
    except SystemExit:
        pass


class MacModelSelectionTests(unittest.TestCase):
    def test_menu_lists_numbered_models_and_valid_choice_processes_it(self):
        from modules.scrap import mac_models

        models = mac_models.MAC_MODELS
        output = io.StringIO()

        with patch("builtins.input", side_effect=["1"]) as prompt, patch.object(
            mac_models, "process_model"
        ) as process, contextlib.redirect_stdout(output):
            run_main(mac_models)

        for number, model in enumerate(models, start=1):
            self.assertIn(str(number), output.getvalue())
            self.assertIn(model, output.getvalue())
        prompt.assert_called_once()
        process.assert_called_once_with(models[0])

    def test_invalid_input_shows_error_and_prompts_again_until_valid_number(self):
        from modules.scrap import mac_models

        models = mac_models.MAC_MODELS
        out_of_range = str(len(models) + 1)
        output = io.StringIO()

        with patch(
            "builtins.input",
            side_effect=["", "abc", "0", out_of_range, str(len(models))],
        ) as prompt, patch.object(
            mac_models, "process_model"
        ) as process, contextlib.redirect_stdout(output):
            run_main(mac_models)

        self.assertEqual(prompt.call_count, 5)
        process.assert_called_once_with(models[-1])

    def test_q_exits_without_processing_model(self):
        from modules.scrap import mac_models

        with patch("builtins.input", side_effect=["q"]), patch.object(
            mac_models, "process_model"
        ) as process, contextlib.redirect_stdout(io.StringIO()):
            run_main(mac_models)

        process.assert_not_called()

    def test_end_of_input_exits_without_processing_model(self):
        from modules.scrap import mac_models

        with patch("builtins.input", side_effect=EOFError), patch.object(
            mac_models, "process_model"
        ) as process, contextlib.redirect_stdout(io.StringIO()):
            run_main(mac_models)

        process.assert_not_called()


if __name__ == "__main__":
    unittest.main()
