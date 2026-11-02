"""Public Python interface for Depencity."""

from depencity._graph.export.dot import to_dot
from depencity._graph.export.json import to_dict, to_json
from depencity._graph.graph_builder import build
from depencity._graph.model.enums import (
    AccessMode,
    EdgeType,
    NodeKind,
    OperationType,
    OutputType,
    ScopeKind,
)
from depencity._graph.model.node import DependencyEdge, Node
from depencity._graph.model.scope import Scope
from depencity._package_graph.package_builder import build_package, build_target
from depencity._profile.classifier import profile, profile_subgraph
from depencity._profile.model.scope_profile import ScopeProfile
from depencity._profile.summary import summarize
from depencity._version import __version__

__all__ = [
    '__version__',
    'build', 'build_package', 'build_target',
    'to_dict', 'to_json', 'to_dot',
    'profile', 'profile_subgraph', 'summarize',
    'Scope', 'Node', 'DependencyEdge', 'ScopeProfile',
    'AccessMode', 'EdgeType', 'NodeKind', 'OperationType', 'OutputType', 'ScopeKind',
]
