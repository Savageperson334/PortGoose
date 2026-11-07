"""PortGoose procedural mutation tests."""
import importlib.util
import unittest
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "scripts" / "mutate.py"
spec = importlib.util.spec_from_file_location("portgoose_mutate", path)
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def state(*types):
    return {"seed": 4, "revision": "t", "operations": [
        {"id": "test-" + str(i), "type": name, "enabled": True}
        for i, name in enumerate(types)]}


class MutationTests(unittest.TestCase):
    def test_base_seed(self):
        x = worker.mutate(state())
        self.assertEqual(len(x["segments"]), 1)
        self.assertEqual(x["stats"]["blooms"], 0)

    def test_fork_and_bloom(self):
        x = worker.mutate(state("fork", "bloom"))
        self.assertEqual(x["stats"]["segments"], 3)
        self.assertEqual(x["stats"]["blooms"], 2)

    def test_operation_order_matters(self):
        a = worker.mutate(state("fork", "grow"))
        b = worker.mutate(state("grow", "fork"))
        self.assertNotEqual(a["segments"], b["segments"])

    def test_toggle_excludes_operation(self):
        x = state("fork", "mirror")
        x["operations"][1]["enabled"] = False
        a = worker.mutate(x)
        self.assertEqual(a["stats"]["segments"], 3)
        self.assertEqual(len(a["history"]), 2)
        self.assertFalse(a["history"][1]["enabled"])

    def test_reseed_alters_growth(self):
        x = state("grow")
        first = worker.mutate(x)["segments"]
        x["seed"] = 929
        self.assertNotEqual(first, worker.mutate(x)["segments"])

    def test_input_validation(self):
        for kind in ("__import__", "run", "exec"):
            with self.assertRaises(ValueError):
                worker.mutate(state(kind))
        with self.assertRaises(ValueError):
            worker.mutate({"seed": True, "operations": []})
        x = state("fork")
        x["operations"][0]["enabled"] = "no"
        with self.assertRaises(ValueError):
            worker.mutate(x)

    def test_caps(self):
        x = state(*(["fork"] * 8 + ["mirror", "bloom"]))
        y = worker.mutate(x)
        self.assertLessEqual(len(y["segments"]), worker.MAX_SEGMENTS)
        self.assertLessEqual(len(y["blooms"]), worker.MAX_BLOOMS)

    def test_determinism(self):
        x = state("grow", "fork", "twist", "bloom", "ripple")
        self.assertEqual(worker.mutate(x), worker.mutate(x))


if __name__ == "__main__":
    unittest.main()
