#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sanity gate for a freshly built transit index (transit-<id>.umti + transit-<id>.json + the builder's log).

Exit 0 when the index is fit to publish, 1 (with the reasons on stdout) otherwise. The weekly workflow deletes the
index when this fails, so the release goes out without a `transit` entry instead of with a broken one.

  check-transit.py --umti F --meta F.json --log build.log [--today YYYY-MM-DD] [--min-stops N] ...
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import sys


def check(umti, meta_path, log_path, today, min_stops, min_lines, min_bytes, max_bytes, min_feeds, min_days):
    errors, warnings = [], []
    size = os.path.getsize(umti)
    if not min_bytes <= size <= max_bytes:
        errors.append(f"size {size} bytes outside {min_bytes}..{max_bytes}")
    with open(meta_path) as f:
        meta = json.load(f)
    if meta.get("size") not in (None, size):
        errors.append(f"sidecar size {meta.get('size')} != file size {size}")
    if meta.get("sha256"):
        h = hashlib.sha256()
        with open(umti, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        if h.hexdigest() != meta["sha256"]:
            errors.append("sidecar sha256 does not match the file")
    # The sidecar carries no counts; the builder prints "stops=N lines=N ..." on its stdout.
    text = open(log_path, errors="replace").read() if log_path and os.path.exists(log_path) else ""
    m = re.search(r"stops=(\d+) lines=(\d+)", text)
    if not m:
        errors.append("no 'stops=N lines=N' line in the build log")
    else:
        stops, lines = int(m.group(1)), int(m.group(2))
        if stops < min_stops:
            errors.append(f"only {stops} stops (minimum {min_stops})")
        if lines < min_lines:
            errors.append(f"only {lines} lines (minimum {min_lines})")
    try:
        valid_to = datetime.date.fromisoformat(meta["validTo"])
        datetime.date.fromisoformat(meta["validFrom"])
        left = (valid_to - today).days
        if left < 0:
            errors.append(f"already expired (validTo {meta['validTo']}, today {today})")
        elif left < min_days:
            warnings.append(f"only {left} day(s) of validity left (validTo {meta['validTo']})")
    except (KeyError, ValueError) as e:
        errors.append(f"bad validFrom/validTo: {e}")
    geo = meta.get("geometry")
    if not isinstance(geo, dict) or not geo:
        errors.append("no geometry block (builder without shapes support?)")
    else:
        patterns = sum(int(v.get("patterns", 0)) for v in geo.values())
        withgeo = sum(int(v.get("withGeometry", 0)) for v in geo.values())
        if patterns == 0 or withgeo == 0:
            errors.append(f"geometry block has no rail pattern with a polyline ({withgeo}/{patterns})")
        elif withgeo * 2 < patterns:
            errors.append(f"only {withgeo}/{patterns} rail patterns have a polyline")
    feeds = meta.get("feeds") or []
    included = [x for x in feeds if x.get("included")]
    if len(included) < min_feeds:
        errors.append(f"only {len(included)} feeds included (minimum {min_feeds}); left out: "
                      + ", ".join(f"{x.get('label')} ({x.get('status')})" for x in feeds if not x.get("included")))
    elif len(included) < len(feeds):
        warnings.append("feeds left out: " + ", ".join(f"{x.get('label')} ({x.get('status')})" for x in feeds if not x.get("included")))
    for x in included:
        if x.get("status") == "projected":
            warnings.append(f"{x.get('label')}: calendar projected from {x.get('projectedFrom')} (old timetables)")
    attr = " ".join(meta.get("attribution") or [])
    if any("CRTM" in (x.get("label") or "") for x in included) and "CRTM" not in attr:
        errors.append("a CRTM feed is included but the attribution does not credit CRTM")
    if any("Renfe" in (x.get("label") or "") for x in included) and "Renfe" not in attr:
        errors.append("a Renfe feed is included but the attribution does not credit Renfe")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--umti", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--log")
    ap.add_argument("--today", help="YYYY-MM-DD (default: today, UTC)")
    ap.add_argument("--min-stops", type=int, default=8000)
    ap.add_argument("--min-lines", type=int, default=400)
    ap.add_argument("--min-bytes", type=int, default=1_500_000)
    ap.add_argument("--max-bytes", type=int, default=25_000_000)
    ap.add_argument("--min-feeds", type=int, default=4)
    ap.add_argument("--min-days", type=int, default=7, help="warn when fewer days of validity remain")
    a = ap.parse_args(argv)
    today = datetime.date.fromisoformat(a.today) if a.today else datetime.datetime.now(datetime.timezone.utc).date()
    errors, warnings = check(a.umti, a.meta, a.log, today, a.min_stops, a.min_lines, a.min_bytes, a.max_bytes, a.min_feeds, a.min_days)
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print("transit sanity gate:", "FAILED" if errors else "passed")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
