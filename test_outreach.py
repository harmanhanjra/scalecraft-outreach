import json, os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
def _load(fname, modname):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(os.path.dirname(os.path.abspath(__file__)), fname))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
ou = _load('scalecraft-outreach.py', 'ou')

def lead(**kw):
    base = {"name": "Test Biz", "city": "Berlin", "website": "", "phone": "", "email": "hi@test.biz", "needs_contact_info": ""}
    base.update(kw); return base

class RenderTests(unittest.TestCase):
    def test_intro_no_website(self):
        d = ou.render(lead(), "intro")
        self.assertIn("don't have a website", d["body"])
        self.assertEqual(d["template"], "intro")
        self.assertIn("Berlin", d["body"])  # city_part

    def test_social_observation(self):
        d = ou.render(lead(website="https://facebook.com/testbiz"), "intro")
        self.assertIn("social", d["body"])

    def test_existing_site_observation(self):
        d = ou.render(lead(website="https://testbiz.io"), "intro")
        self.assertIn("could be doing a lot more", d["body"])

    def test_all_templates_render(self):
        for t in ou.TEMPLATES:
            d = ou.render(lead(), t)
            self.assertIn("Test Biz", d["body"])
            self.assertTrue(d["subject"])

    def test_missing_contact_flags(self):
        d = ou.render(lead(email="", needs_contact_info="phone,email"), "intro")
        self.assertIn("phone", d["missing"])
        self.assertIn("email", d["missing"])

class StateTests(unittest.TestCase):
    def test_skip_already_drafted(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump([lead(name="A"), lead(name="B")], f); f.close()
        state = tempfile.NamedTemporaryFile(suffix=".json", delete=False); state.close()
        try:
            import io, contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc1 = ou.main(["--in", f.name, "--status", state.name, "--out", state.name + ".drafts"])
                rc2 = ou.main(["--in", f.name, "--status", state.name, "--out", state.name + ".drafts2"])
            self.assertEqual(rc1, 0); self.assertEqual(rc2, 0)
            d1 = json.load(open(state.name + ".drafts")); d2 = json.load(open(state.name + ".drafts2"))
            self.assertEqual(d1["count"], 2)
            self.assertEqual(d2["count"], 0)  # all skipped on second run
        finally:
            for p in (f.name, state.name, state.name + ".drafts", state.name + ".drafts2"):
                if os.path.exists(p): os.unlink(p)

    def test_load_state_missing_file(self):
        self.assertEqual(ou.load_state("/nonexistent-state.json"), {"sent": [], "drafted": []})

if __name__ == "__main__":
    unittest.main()
