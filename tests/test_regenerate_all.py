"""The regenerate_all orchestrator must cover every generator in the manifest.

regenerate_all.py derives its plan from scripts/generators.json at runtime, so
it can't silently drift — but a broken import or a manifest schema change would
still slip past unnoticed. This pins the contract: the derived plan names every
distinct generator script the manifest lists, and each is a real file.
"""
import json
import os

import regenerate_all  # scripts/ is on sys.path via conftest
from conftest import ROOT


def test_plan_covers_every_manifest_generator():
    with open(os.path.join(ROOT, "scripts", "generators.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    manifest_scripts = {e["script"] for e in manifest["generators"]}
    plan_scripts = {script for script, _sources in regenerate_all.load_plan()}
    assert plan_scripts == manifest_scripts, (
        "regenerate_all's plan diverged from generators.json: "
        f"missing={manifest_scripts - plan_scripts} extra={plan_scripts - manifest_scripts}")


def test_plan_scripts_all_exist():
    for script, _sources in regenerate_all.load_plan():
        assert os.path.isfile(os.path.join(ROOT, script)), f"missing generator: {script}"
