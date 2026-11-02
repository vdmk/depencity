from enum import Enum


class ScopeKind(str, Enum):
    ROOT = 'root'
    MODULE = 'module'
    FUNCTION = 'function'
    CLASS = 'class'
    COMPREHENSION = 'comprehension'
    BUILTINS = 'builtins'


class EdgeType(str, Enum):
    DATA = 'data'
    ITERATION = 'iteration'
    PREDICATE = 'predicate'
    BINDING = 'binding'
    DECLARATION = 'declaration'

    @property
    def is_dependency(self) -> bool:
        return self in (EdgeType.DATA, EdgeType.ITERATION, EdgeType.PREDICATE)


class NodeKind(str, Enum):
    """Language-independent role of a dependency graph node."""

    VARIABLE = 'variable'
    RESULT = 'result'
    YIELD_FROM_RESULT = 'yield_from_result'
    IMPORT_TARGET = 'import_target'
    UNRESOLVED_VALUE = 'unresolved_value'
    BINDING = 'binding'
    OPERATION = 'operation'
    CALL = 'call'
    REFERENCE = 'reference'
    CONDITION = 'condition'
    COMPREHENSION = 'comprehension'
    SUBSCRIPT = 'subscript'

    @property
    def is_value(self) -> bool:
        return self in (
            NodeKind.VARIABLE, NodeKind.RESULT, NodeKind.YIELD_FROM_RESULT,
            NodeKind.IMPORT_TARGET, NodeKind.UNRESOLVED_VALUE,
        )


class OperationType(str, Enum):
    TRANSFORM = 'transform'
    EXTRACT = 'extract'
    CONTAINER = 'container'
    MUTATION = 'mutation'
    RAISE = 'raise'
    ASSERT = 'assert'


class AccessMode(str, Enum):
    """How a node accesses the data it represents."""

    READ = 'read'
    WRITE = 'write'


class OutputType(str, Enum):
    RETURN = 'return'
    YIELD = 'yield'
    RESULT = 'result'
