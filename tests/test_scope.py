from depencity._graph.model.enums import ScopeKind
from depencity._graph.model.ir import NodeRecord, ScopeRecord
from depencity._graph.model.scope import Scope, create_unique_id


def test_capture_binding_environment_handles_empty_inconsistent_scope():
    # This deliberately violates the ownership invariant to cover the loop's
    # zero-iteration branch; source-derived scopes cannot produce this state.
    scope = ScopeRecord('f', ScopeKind.FUNCTION, None)
    visible = NodeRecord('value', scope)
    before = NodeRecord('before', scope)

    assert scope.capture_binding_environment({'value': [visible]}, before).bindings == {}


def test_walk_scopes_preserves_child_order_without_recursion():
    root = Scope('__root__', ScopeKind.ROOT, None)
    current = root
    expected = [root]
    for index in range(1200):
        child = Scope(str(index), ScopeKind.FUNCTION, current)
        current.children.append(child)
        expected.append(child)
        current = child
    sibling = Scope('sibling', ScopeKind.MODULE, root)
    root.children.append(sibling)

    actual = list(root.walk_scopes())

    assert [id(scope) for scope in actual] == [id(scope) for scope in [*expected, sibling]]


def test_create_unique_id_skips_used_suffixes():
    assert create_unique_id('scope', {'scope', 'scope#2', 'scope#3'}) == 'scope#4'
