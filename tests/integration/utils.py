from pathlib import Path

FIXTURES_ROOT = Path(__file__).parents[1] / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURES_ROOT / name).read_text()


def walk_scope_tree(scopes: list[dict]):
    pending = list(reversed(scopes))
    while pending:
        scope = pending.pop()
        yield scope
        pending.extend(reversed(scope.get('children', [])))


def assert_fixture_sources_compile(fixture_path: Path) -> None:
    excluded_sources = {
        "builder/invalid_syntax/input.py",
        "builder/unbound_nonlocal/input.py",
        "package/ignored_sources/venv/broken.py",
    }
    for source_path in fixture_path.rglob("*.py"):
        if not source_path.is_file():
            continue
        relative_path = source_path.relative_to(FIXTURES_ROOT).as_posix()
        if relative_path in excluded_sources:
            continue
        compile(source_path.read_bytes(), str(source_path), "exec")


def assert_graph_integrity(document: dict) -> None:
    nodes = document['nodes']
    node_ids = [node['id'] for node in nodes]
    assert len(node_ids) == len(set(node_ids))

    node_id_set = set(node_ids)
    dependency_edges = [
        (dependency, node['id'])
        for node in nodes
        for dependency in node['dependencies']
    ]
    expected_edges = set(dependency_edges)
    edges = [
        (edge['source'], edge['target'], edge['edge_type'])
        for edge in document['edges']
    ]
    assert len(dependency_edges) == len(expected_edges)
    assert len(edges) == len(set(edges))
    assert {
        (source, target) for source, target, edge_type in edges
        if edge_type in ('data', 'iteration', 'predicate')
    } == expected_edges
    scope_ids = {scope['id'] for scope in document['scopes']}
    entity_ids = node_id_set | scope_ids
    assert all(source in entity_ids and target in entity_ids for source, target, _ in edges)
