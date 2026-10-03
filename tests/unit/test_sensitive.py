"""Unit tests for the Sensitive-Value Filter (TASK-008)."""

from __future__ import annotations

from docsync.model import (
    UNAVAILABLE,
    ClassDoc,
    FunctionDoc,
    ModuleDoc,
    ParameterDoc,
)
from docsync.sensitive import REDACTED, filter_module, redact


def test_redact_pem_private_key_block():
    text = "before -----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAKCAQ==\n-----END RSA PRIVATE KEY----- after"
    result = redact(text)
    assert REDACTED in result
    assert "MIIBogIBAAKCAQ" not in result


def test_redact_aws_access_key_id():
    result = redact("key=AKIAABCDEFGHIJKLMNOP")
    assert "AKIAABCDEFGHIJKLMNOP" not in result
    assert REDACTED in result


def test_redact_stripe_style_secret_key():
    result = redact("sk_live_51H8x9examplekey")
    assert "sk_live_51H8x9examplekey" not in result
    assert REDACTED in result


def test_redact_github_token():
    result = redact("ghp_1234567890abcdef1234567890abcdef1234")
    assert "ghp_1234567890abcdef" not in result


def test_redact_credentials_embedded_in_url():
    result = redact("dsn='postgres://user:pw@host/db'")
    assert "user:pw@host" not in result
    assert REDACTED in result


def test_redact_keyword_value_pair_in_free_text():
    result = redact('password="hunter2"')
    assert "hunter2" not in result
    assert REDACTED in result


def test_redact_leaves_non_sensitive_text_untouched():
    text = "Computes the sum of two integers."
    assert redact(text) == text


def test_redact_passes_through_sentinel():
    assert redact(UNAVAILABLE) is UNAVAILABLE


def test_filter_parameter_default_secret_by_keyword_name():
    module = ModuleDoc(
        path="pkg/a.py",
        functions=[
            FunctionDoc(
                name="login",
                parameters=[ParameterDoc(name="password", default="'hunter2'")],
            )
        ],
    )
    filtered = filter_module(module)
    assert filtered.functions[0].parameters[0].default == REDACTED


def test_filter_decorator_call_string_literal_argument_secret():
    module = ModuleDoc(
        path="pkg/a.py",
        functions=[
            FunctionDoc(
                name="call_api",
                decorators=["requires_api_key('sk-live-abc123xyz')"],
            )
        ],
    )
    filtered = filter_module(module)
    decorator_text = filtered.functions[0].decorators[0]
    assert "sk-live-abc123xyz" not in decorator_text
    assert REDACTED in decorator_text


def test_filter_class_decorator_credential_in_url():
    module = ModuleDoc(
        path="pkg/a.py",
        classes=[
            ClassDoc(
                name="Store",
                decorators=["cache(dsn='postgres://user:pw@host/db')"],
            )
        ],
    )
    filtered = filter_module(module)
    decorator_text = filtered.classes[0].decorators[0]
    assert "user:pw@host" not in decorator_text


def test_redact_keyword_value_pair_for_compound_identifiers():
    """SEC-01 regression: underscore-joined compound identifiers must be
    recognized, not just the bare keyword -- \\b fails to find a boundary
    before 'password' in 'db_password' because '_' is a \\w character."""
    for text, leaked in [
        ('db_password="hunter2"', "hunter2"),
        ("client_secret='abc123xyz'", "abc123xyz"),
        ('admin_token="tok-999"', "tok-999"),
        ("my_api_key='sk-xyz-000'", "sk-xyz-000"),
    ]:
        result = redact(text)
        assert leaked not in result, f"failed to redact: {text!r}"
        assert REDACTED in result


def test_filter_parameter_default_secret_by_compound_keyword_name():
    """SEC-01 regression: parameter-name heuristic must match compound
    identifiers like db_password/client_secret/admin_token/my_api_key."""
    for name in ("db_password", "client_secret", "admin_token", "my_api_key"):
        module = ModuleDoc(
            path="pkg/a.py",
            functions=[
                FunctionDoc(
                    name="configure",
                    parameters=[ParameterDoc(name=name, default="'sensitive-value'")],
                )
            ],
        )
        filtered = filter_module(module)
        assert filtered.functions[0].parameters[0].default == REDACTED, (
            f"failed to redact parameter named {name!r}"
        )


def test_filter_parameter_default_not_redacted_for_unrelated_word():
    """SEC-01 regression (negative control): the fix must not broaden
    matching to unrelated ordinary words that merely share a substring."""
    module = ModuleDoc(
        path="pkg/a.py",
        functions=[
            FunctionDoc(
                name="configure",
                parameters=[
                    ParameterDoc(name="mypasswordmanager", default="'not-a-secret'"),
                    ParameterDoc(name="username", default="'alice'"),
                ],
            )
        ],
    )
    filtered = filter_module(module)
    assert filtered.functions[0].parameters[0].default == "'not-a-secret'"
    assert filtered.functions[0].parameters[1].default == "'alice'"


def test_redact_leaves_unrelated_word_in_free_text_untouched():
    """SEC-01 regression (negative control): free text containing an
    unrelated word must not be redacted."""
    text = "The password manager stores nothing here; passwordless auth only."
    result = redact(text)
    assert result == text


def test_filter_redacts_before_hash_or_render_would_see_it():
    """Confirms redaction happens on the model itself (before any downstream
    hashing/rendering step consumes it) -- not merely at render time."""
    module = ModuleDoc(
        path="pkg/a.py",
        docstring="Uses api_key='sk-live-shouldnotleak12345' internally.",
    )
    filtered = filter_module(module)
    assert "sk-live-shouldnotleak12345" not in filtered.docstring
    assert filtered.docstring != module.docstring
