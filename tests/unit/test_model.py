from docsync.model import (
    NOT_APPLICABLE,
    UNAVAILABLE,
    ClassDoc,
    FunctionDoc,
    ModuleDoc,
    ParameterDoc,
    ParseError,
)


def test_module_doc_defaults():
    m = ModuleDoc(path="pkg/a.py")
    assert m.docstring is UNAVAILABLE
    assert m.classes == []
    assert m.functions == []
    assert m.errors == []


def test_class_doc_construction():
    c = ClassDoc(name="Foo", docstring="A class", decorators=["@dataclass"])
    assert c.name == "Foo"
    assert c.docstring == "A class"
    assert c.methods == []


def test_function_doc_construction():
    f = FunctionDoc(
        name="bar",
        docstring="Does a thing",
        decorators=["@staticmethod"],
        parameters=[ParameterDoc(name="x", annotation="int", default="0")],
        return_annotation="int",
    )
    assert f.name == "bar"
    assert f.parameters[0].name == "x"
    assert f.return_annotation == "int"


def test_parameter_doc_sentinel_distinction():
    # A parameter with no annotation: conceptually could have had one, but doesn't.
    p_no_annotation = ParameterDoc(name="x")
    assert p_no_annotation.annotation is UNAVAILABLE
    # A parameter with no default: NOT_APPLICABLE, not a gap in analysis.
    assert p_no_annotation.default is NOT_APPLICABLE


def test_sentinels_are_distinguishable_and_falsy():
    assert UNAVAILABLE is not NOT_APPLICABLE
    assert not UNAVAILABLE
    assert not NOT_APPLICABLE
    assert repr(UNAVAILABLE) == "UNAVAILABLE"
    assert repr(NOT_APPLICABLE) == "NOT_APPLICABLE"


def test_parse_error_fields():
    e = ParseError(path="pkg/bad.py", stage="parse", message="invalid syntax")
    assert e.path == "pkg/bad.py"
    assert e.stage == "parse"
    assert e.message == "invalid syntax"


def test_module_doc_no_module_level_constant_field():
    # Resolves DR-004: ModuleDoc must have exactly these fields, no
    # module-level-constant field, since FR-006 does not request one.
    m = ModuleDoc(path="pkg/a.py")
    field_names = {f for f in m.__dataclass_fields__}
    assert field_names == {"path", "docstring", "classes", "functions", "errors"}
