"""Built-in tests, no dependencies."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts" / "process_log.py"
spec = importlib.util.spec_from_file_location("sandbox_worker", path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


class SandboxTests(unittest.TestCase):
    def test_calculation(self):
        self.assertEqual(worker.evaluate("(12+8)*3"), 60)
        self.assertEqual(worker.evaluate("sqrt(144) + 2^3"), 20)

    def test_plot(self):
        result = worker.process([{"id": "a", "message": "plot sin(x)"}])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["points"]), 81)
        self.assertAlmostEqual(result["points"][40]["y"], 0)

    def test_last_command_wins(self):
        result = worker.process([
            {"id": "a", "message": "calc 1+1"},
            {"id": "b", "message": "Howdy"},
            {"id": "c", "message": "calc 3*7"},
        ])
        self.assertEqual(result["source_id"], "c")
        self.assertEqual(result["value"], 21)

    def test_noncommand_is_ignored(self):
        self.assertEqual(worker.process([{"message": "Howdy"}])["status"], "idle")

    def test_reject_python_code(self):
        for expr in ["__import__('os').system('echo nope')", "x.__class__", "[1,2,3]", "1 if True else 0", "open('file')"]:
            with self.subTest(expr=expr), self.assertRaises((ValueError, SyntaxError)):
                worker.evaluate(expr)

    def test_no_unbounded_power(self):
        with self.assertRaises(ValueError):
            worker.evaluate("10**1000")

    def test_division_by_zero_is_error_status(self):
        result = worker.process([{"id": "a", "message": "calc 4/0"}])
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
