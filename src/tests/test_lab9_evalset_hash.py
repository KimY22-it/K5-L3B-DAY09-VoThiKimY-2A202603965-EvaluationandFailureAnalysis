"""Eval set hashes and builders must agree on Windows and Linux checkouts."""

import hashlib
import json

import pytest

from lab9 import evalset

pytestmark = pytest.mark.student


@pytest.mark.parametrize("ending", [b"\n", b"\r\n"])
def test_evalset_hash_matches_lf_bytes(tmp_path, ending):
    canonical = b'{"item_id":"E-001"}\n{"item_id":"E-002"}\n'
    path = tmp_path / "items.jsonl"
    path.write_bytes(canonical.replace(b"\n", ending))
    assert evalset.sha12(path) == hashlib.sha256(canonical).hexdigest()[:12]


def test_hash_still_detects_changed_input(tmp_path):
    path = tmp_path / "items.jsonl"
    path.write_bytes(b'{"claim_id":"C-001"}\r\n')
    original = evalset.sha12(path)
    path.write_bytes(b'{"claim_id":"C-002"}\n')
    assert evalset.sha12(path) != original


def test_both_builders_write_lf(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "claims.jsonl"
    source.write_text(json.dumps({"claim_id": "C-001", "matrix_id": "T01",
                                  "expected": {"status": "denied", "refund_vnd": 0}}), encoding="utf-8")
    evalset.build(source)
    pack = tmp_path / "pack.json"
    pack.write_text('{"claims": []}', encoding="utf-8")
    mapping = tmp_path / "mapping.yaml"
    mapping.write_text("{}", encoding="utf-8")
    evalset.build_v2(evalset.ITEMS, evalset.LABELS, pack, mapping)
    for path in (evalset.ITEMS, evalset.ITEMS_V2):
        assert path.read_bytes().endswith(b"\n")
        assert b"\r\n" not in path.read_bytes()
