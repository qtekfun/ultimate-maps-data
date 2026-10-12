# SPDX-License-Identifier: GPL-3.0-or-later
import datetime
import hashlib
import importlib.util
import json
import os
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("check_transit", os.path.join(os.path.dirname(__file__), "check-transit.py"))
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)

TODAY = datetime.date(2026, 10, 12)


class Gate(unittest.TestCase):
    def run_gate(self, meta_patch=None, log="stops=12955 lines=704 patterns=1", payload=b"x" * 2_000_000, **kw):
        d = tempfile.mkdtemp()
        umti = os.path.join(d, "transit-madrid.umti")
        open(umti, "wb").write(payload)
        meta = {"id": "madrid", "validFrom": "2026-10-12", "validTo": "2026-11-10", "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "attribution": ["Powered by CRTM", "Renfe Operadora, CC BY 4.0"],
                "geometry": {"metro": {"patterns": 30, "withGeometry": 30}, "train": {"patterns": 88, "withGeometry": 88}},
                "feeds": [{"label": f"CRTM {i}", "included": True, "status": "ok"} for i in range(5)]
                + [{"label": "Renfe Cercanias", "included": True, "status": "ok"}]}
        meta.update(meta_patch or {})
        mp = os.path.join(d, "transit-madrid.json")
        json.dump(meta, open(mp, "w"))
        lp = os.path.join(d, "build.log")
        open(lp, "w").write(log)
        return ct.check(umti, mp, lp, kw.get("today", TODAY), 8000, 400, 1_500_000, 25_000_000, 4, 7)

    def test_good(self):
        e, w = self.run_gate()
        self.assertEqual(e, [])

    def test_expired(self):
        e, _ = self.run_gate({"validTo": "2026-10-01"})
        self.assertTrue(any("expired" in x for x in e))

    def test_few_stops(self):
        e, _ = self.run_gate(log="stops=120 lines=3")
        self.assertEqual(len(e), 2)

    def test_missing_log_counts(self):
        e, _ = self.run_gate(log="nothing")
        self.assertTrue(any("stops=N" in x for x in e))

    def test_no_geometry(self):
        e, _ = self.run_gate({"geometry": None})
        self.assertTrue(any("geometry" in x for x in e))

    def test_too_small(self):
        e, _ = self.run_gate(payload=b"x" * 100)
        self.assertTrue(any("size" in x for x in e))

    def test_sha_mismatch(self):
        e, _ = self.run_gate({"sha256": "0" * 64})
        self.assertTrue(any("sha256" in x for x in e))

    def test_too_few_feeds(self):
        e, _ = self.run_gate({"feeds": [{"label": "CRTM", "included": True}, {"label": "x", "included": False, "status": "expired"}]})
        self.assertTrue(any("feeds included" in x for x in e))

    def test_near_expiry_warns(self):
        e, w = self.run_gate({"validTo": "2026-10-15"})
        self.assertEqual(e, [])
        self.assertTrue(any("validity left" in x for x in w))


if __name__ == "__main__":
    unittest.main()
