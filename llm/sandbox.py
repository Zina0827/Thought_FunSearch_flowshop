from __future__ import annotations

import ast
from types import FunctionType
from typing import Any


FORBIDDEN_NODES = (
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
    pass


class SafetyVisitor(ast.NodeVisitor):
    def visit(self, node: ast.AST) -> Any:
        if isinstance(node, FORBIDDEN_NODES):
            raise SandboxError(f'Forbidden syntax: {type(node).__name__}')
        return super().visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in FORBIDDEN_NAMES:
            raise SandboxError(f'Forbidden name: {node.id}')
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        if node.attr.startswith('__'):
            raise SandboxError('Dunder attributes are not allowed.')
        self.generic_visit(node)


def validate_code(code: str) -> ast.Module:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise SandboxError(f'Syntax error: {exc}') from exc
    SafetyVisitor().visit(tree)
    return tree


def load_priority_function(code: str) -> FunctionType:
    tree = validate_code(code)
    namespace: dict[str, Any] = {}
    safe_globals = {'__builtins__': ALLOWED_BUILTINS}
    compiled = compile(tree, filename='<candidate>', mode='exec')
    exec(compiled, safe_globals, namespace)
    fn = namespace.get('priority') or safe_globals.get('priority')
    if not callable(fn):
        raise SandboxError('Candidate code must define a callable named `priority`.')
    return fn
