"""Documentation model: plain-data classes representing FR-006's extracted information.

Two distinct sentinels are used deliberately (architecture.md Section 9):
UNAVAILABLE means a value is conceptually present in source but could not be
statically determined (e.g. no return annotation given). NOT_APPLICABLE means
the concept simply does not apply (e.g. a parameter with no default value).
"""

from __future__ import annotations

from dataclasses import dataclass, field


class _Sentinel:
    def __init__(self, name: str) -> None:
        self._name = name

    def __repr__(self) -> str:
        return self._name

    def __bool__(self) -> bool:
        return False


UNAVAILABLE = _Sentinel("UNAVAILABLE")
NOT_APPLICABLE = _Sentinel("NOT_APPLICABLE")


@dataclass
class ParseError:
    path: str
    stage: str
    message: str


@dataclass
class ParameterDoc:
    name: str
    annotation: object = UNAVAILABLE
    default: object = NOT_APPLICABLE


@dataclass
class FunctionDoc:
    name: str
    docstring: object = UNAVAILABLE
    decorators: list[str] = field(default_factory=list)
    parameters: list[ParameterDoc] = field(default_factory=list)
    return_annotation: object = UNAVAILABLE


@dataclass
class ClassDoc:
    name: str
    docstring: object = UNAVAILABLE
    decorators: list[str] = field(default_factory=list)
    methods: list[FunctionDoc] = field(default_factory=list)


@dataclass
class ModuleDoc:
    path: str
    docstring: object = UNAVAILABLE
    classes: list[ClassDoc] = field(default_factory=list)
    functions: list[FunctionDoc] = field(default_factory=list)
    errors: list[ParseError] = field(default_factory=list)
