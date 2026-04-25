"""Validate and load generated priority functions in a restricted namespace."""

from __future__ import annotations

import ast
from types import FunctionType
from typing import Any


FORBIDDEN_NODES = (
    # Generated heuristics only need arithmetic and loops; blocking imports,
    # classes, and control-flow escape hatches keeps execution predictable.
    ast.Import,
    ast.ImportFrom,
    ast.With,
    ast.Try,
    ast.Raise,
    ast.ClassDef,
    ast.Global,
    ast.Nonlocal,
    ast.Lambda,
)

FORBIDDEN_NAMES = {
    # Introspection and dynamic execution would let generated code bypass the
    # narrow namespace used for candidate evaluation.
    '__import__',
    'eval',
    'exec',
    'open',
    'compile',
    'input',
    'globals',
    'locals',
    'vars',
    'dir',
    'getattr',
    'setattr',
    'delattr',
}

ALLOWED_BUILTINS = {
    'abs': abs,
    'min': min,
    'max': max,
    'sum': sum,
    'len': len,
    'range': range,
    'enumerate': enumerate,
    'float': float,
    'int': int,
}


class SandboxError(RuntimeError):
    """Raised when generated code violates sandbox rules or lacks ``priority``."""

    pass


class SafetyVisitor(ast.NodeVisitor):
    """AST visitor that rejects syntax and names outside the sandbox policy."""

    def visit(self, node: ast.AST) -> Any:
        """Reject forbidden node types before recursively visiting children."""
        if isinstance(node, FORBIDDEN_NODES):
            raise SandboxError(f'Forbidden syntax: {type(node).__name__}')
        return super().visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        """Reject access to forbidden built-in or introspection names."""
        if node.id in FORBIDDEN_NAMES:
            raise SandboxError(f'Forbidden name: {node.id}')
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        """Reject dunder attribute access on generated-code objects."""
        if node.attr.startswith('__'):
            raise SandboxError('Dunder attributes are not allowed.')
        self.generic_visit(node)


def validate_code(code: str) -> ast.Module:
    """Parse generated code and return its AST if it passes safety checks."""
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f'Syntax error: {exc}') from exc
    SafetyVisitor().visit(tree)
    return tree


def load_priority_function(code: str) -> FunctionType:
    """Compile safe generated code and return its callable ``priority`` function."""
    tree = validate_code(code)
    namespace: dict[str, Any] = {}
    # Candidate code receives a tiny builtin set so failures are deterministic and
    # generated functions cannot touch files, imports, or the surrounding process.
    safe_globals = {'__builtins__': ALLOWED_BUILTINS}
    compiled = compile(tree, filename='<candidate>', mode='exec')
    exec(compiled, safe_globals, namespace)
    fn = namespace.get('priority') or safe_globals.get('priority')
    if not callable(fn):
        raise SandboxError('Candidate code must define a callable named `priority`.')
    return fn
