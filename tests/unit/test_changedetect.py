"""Unit tests for the Change Detector (TASK-009)."""

from __future__ import annotations

from docsync.changedetect import (
    build_hash_table,
    compute_file_hash,
    has_changed,
    parse_previous_hash_table,
    serialize_hash_table,
)
from docsync.model import FunctionDoc, ModuleDoc


def test_signature_change_triggers_regeneration():
    before = ModuleDoc(path="pkg/a.py", functions=[FunctionDoc(name="f", return_annotation="int")])
    after = ModuleDoc(path="pkg/a.py", functions=[FunctionDoc(name="f", return_annotation="str")])
    assert compute_file_hash(before) != compute_file_hash(after)


def test_docstring_change_triggers_regeneration():
    before = ModuleDoc(path="pkg/a.py", docstring="old docs")
    after = ModuleDoc(path="pkg/a.py", docstring="new docs")
    assert compute_file_hash(before) != compute_file_hash(after)


def test_body_only_change_does_not_affect_hash():
    # The model never carries body statements (TASK-007), so two modules
    # built from source that differs only in function-body content, but
    # produce an identical extracted model, must hash identically.
    a = ModuleDoc(path="pkg/a.py", functions=[FunctionDoc(name="f", docstring="doc")])
    b = ModuleDoc(path="pkg/a.py", functions=[FunctionDoc(name="f", docstring="doc")])
    assert compute_file_hash(a) == compute_file_hash(b)


def test_new_file_triggers_regeneration():
    previous = {"pkg/a.py": "hash-a"}
    current = {"pkg/a.py": "hash-a", "pkg/b.py": "hash-b"}
    assert has_changed(previous, current) is True


def test_removed_file_triggers_regeneration():
    previous = {"pkg/a.py": "hash-a", "pkg/b.py": "hash-b"}
    current = {"pkg/a.py": "hash-a"}
    assert has_changed(previous, current) is True


def test_identical_tables_produce_no_change():
    previous = {"pkg/a.py": "hash-a", "pkg/b.py": "hash-b"}
    current = {"pkg/a.py": "hash-a", "pkg/b.py": "hash-b"}
    assert has_changed(previous, current) is False


def test_build_hash_table_keyed_by_module_path():
    modules = [ModuleDoc(path="pkg/a.py"), ModuleDoc(path="pkg/b.py")]
    table = build_hash_table(modules)
    assert set(table.keys()) == {"pkg/a.py", "pkg/b.py"}


def test_parse_previous_hash_table_from_banner():
    text = 'header\n<!-- docsync:v1 sha256={"pkg/a.py": "abc123"} -->\nmore text\n'
    table = parse_previous_hash_table(text)
    assert table == {"pkg/a.py": "abc123"}


def test_parse_previous_hash_table_absent_marker_is_empty():
    assert parse_previous_hash_table("no marker here") == {}
    assert parse_previous_hash_table(None) == {}


def test_parse_previous_hash_table_malformed_json_is_empty():
    text = "<!-- docsync:v1 sha256={not valid json} -->"
    assert parse_previous_hash_table(text) == {}


def test_serialize_hash_table_sorted_keys_deterministic():
    table = {"pkg/b.py": "2", "pkg/a.py": "1"}
    assert serialize_hash_table(table) == '{"pkg/a.py": "1", "pkg/b.py": "2"}'
