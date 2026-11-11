"""Compact numeric summaries for humans and refactoring agents."""

from __future__ import annotations

import json
from collections.abc import Sequence
from importlib.metadata import version
from typing import Any

from depencity._graph.model.scope import Scope, create_scope_ids
from depencity._profile.classifier import profile, profile_subgraph
from depencity._profile.model.scope_profile import ScopeProfile


def _profile_output(profile: dict, metrics: set[str] | None = None) -> dict:
    result: dict[str, Any] = {}
    for name, value in profile.items():
        name = name.replace('__', '.')
        if metrics is not None and name not in metrics:
            continue
        if isinstance(value, dict):
            result[name] = {str(key): item for key, item in value.items()}
        else:
            result[name] = value
    return result


def summarize(
    root: Scope, scope_id: str | None = None,
    include_children: bool = False, include_parent: bool = False,
    metrics: Sequence[str] | None = None,
    depth: int | None = None,
    include_own_profile: bool = False,
) -> dict:
    _validate_metrics(metrics)
    scopes = list(root.walk_scopes())
    scope_ids = create_scope_ids(scopes)
    scope_records = [
        {
            'id': scope_ids[id(scope)],
            'kind': scope.kind.value,
            'parent': scope_ids.get(id(scope.parent)),
        }
        for scope in scopes
    ]
    selected = _select_scopes(
        scope_records, scope_id, include_children, include_parent, depth
    )
    scopes_by_id = {scope_ids[id(scope)]: scope for scope in scopes}
    metric_filter = set(metrics) if metrics is not None else None
    include_paths = metric_filter is None or any(
        name.startswith('graph.paths.') for name in metric_filter
    )
    include_cycles = (
        metric_filter is None or any(
            name.startswith('graph.cyclic_components.') for name in metric_filter
        )
    )
    scope_metrics: dict[int, dict] = {}
    direct = {}
    if include_own_profile and metrics != []:
        for item in selected:
            scope = scopes_by_id[item['id']]
            direct[id(scope)] = profile(
                scope, include_paths=include_paths, include_cycles=include_cycles,
                scope_metrics=scope_metrics,
            )
    measured = []
    for item in selected:
        scope = scopes_by_id[item['id']]
        direct_output = {}
        subgraph_output = {}
        if metrics != []:
            if include_own_profile:
                direct_output = _profile_dict(direct[id(scope)], metric_filter)
            if not scope.children and include_own_profile:
                subgraph = direct[id(scope)]
            else:
                subgraph = profile_subgraph(
                    scope, scope_metrics,
                    include_paths=include_paths, include_cycles=include_cycles,
                )
            subgraph_output = _profile_dict(subgraph, metric_filter)
        measured.append({
            **item,
            'own_profile': direct_output,
            'profile': subgraph_output,
        })
    return _format_summary(
        measured, metric_filter, include_own_profile, scope_records
    )


def serialize_summary(summary: dict) -> str:
    """Serialize a profile summary consistently across CLI and MCP output."""
    return json.dumps(summary, indent=2, sort_keys=True)


def summarize_document(
    document: dict, scope_id: str | None = None,
    include_children: bool = False, include_parent: bool = False,
    metrics: Sequence[str] | None = None,
    depth: int | None = None,
    include_own_profile: bool = False,
) -> dict:
    """Return measurements for the selected scope tree."""
    _validate_metrics(metrics)
    selected = _select_scopes(
        document.get('scopes', []), scope_id, include_children, include_parent,
        depth,
    )
    return _format_summary(
        selected, set(metrics) if metrics is not None else None,
        include_own_profile, document.get('scopes', []),
    )


def _select_scopes(
    all_scopes: list[dict], scope_id: str | None,
    include_children: bool, include_parent: bool,
    depth: int | None,
) -> list[dict]:
    if depth is not None and (isinstance(depth, bool) or not isinstance(depth, int) or depth < 0):
        raise ValueError('depth must be a non-negative integer or None')
    selected = all_scopes
    if scope_id is not None:
        selected = [scope for scope in all_scopes if scope.get('id') == scope_id]
        if not selected:
            raise ValueError(f'unknown scope: {scope_id}')
    children_by_parent: dict[str, list[str]] = {}
    for scope in all_scopes:
        parent = scope.get('parent')
        if parent is not None:
            children_by_parent.setdefault(parent, []).append(scope['id'])
    if scope_id is not None:
        selected_scope = selected[0]
        selected_ids = {scope_id}
        if include_parent and selected_scope.get('parent') is not None:
            selected_ids.add(selected_scope['parent'])
        if include_children:
            selected_ids.update(children_by_parent.get(scope_id, []))
        selected = [scope for scope in all_scopes if scope['id'] in selected_ids]
    scopes_by_id = {scope['id']: scope for scope in selected}
    result = []
    pending = [
        (scope, 0) for scope in reversed(selected)
        if scope.get('parent') not in scopes_by_id
    ]
    while pending:
        scope, level = pending.pop()
        result.append(scope)
        if depth is None or level < depth:
            pending.extend(
                (scopes_by_id[child], level + 1)
                for child in reversed(children_by_parent.get(scope['id'], []))
                if child in scopes_by_id
            )
    return result


def _format_summary(
    selected: list[dict],
    metric_filter: set[str] | None,
    include_own_profile: bool,
    all_scopes: list[dict],
) -> dict:
    scopes_by_id = {}
    result: dict[str, Any] = {
        'version': version('depencity'),
        'scopes': [],
    }
    for scope in selected:
        item = {
            'id': scope['id'],
            'kind': scope['kind'],
            'profile': _profile_output(scope['profile'], metric_filter),
        }
        if include_own_profile:
            item['own_profile'] = _profile_output(scope.get('own_profile', {}), metric_filter)
        scopes_by_id[scope['id']] = item
    for scope in selected:
        item = scopes_by_id[scope['id']]
        parent = scopes_by_id.get(scope.get('parent'))
        if parent is None:
            result['scopes'].append(item)
        else:
            parent.setdefault('children', []).append(item)
    scopes_by_id = {scope['id']: scope for scope in all_scopes}
    children_by_parent: dict[str, list[str]] = {}
    for scope in all_scopes:
        if scope.get('parent') is not None:
            children_by_parent.setdefault(scope['parent'], []).append(scope['id'])
    measured_ids = set()
    pending = [scope['id'] for scope in selected]
    while pending:
        scope_id = pending.pop()
        if scope_id in measured_ids or scope_id not in scopes_by_id:
            continue
        measured_ids.add(scope_id)
        pending.extend(children_by_parent.get(scope_id, []))
    scope_counts = {'total': len(measured_ids)}
    for scope_id in measured_ids:
        scope = scopes_by_id[scope_id]
        scope_counts[scope['kind']] = scope_counts.get(scope['kind'], 0) + 1
    result['scope_counts'] = scope_counts
    return result


def _profile_dict(value: ScopeProfile, metrics: set[str] | None = None) -> dict:
    result = {
        name: item for name, item in vars(value).items()
        if metrics is None or name.replace('__', '.') in metrics
    }
    distribution = 'graph__paths__data__length__distribution'
    if distribution in result:
        result[distribution] = {
            str(depth): count for depth, count in sorted(result[distribution].items())
        }
    return result


def _validate_metrics(metrics: Sequence[str] | None) -> None:
    if metrics is None:
        return
    known = {name.replace('__', '.') for name in vars(ScopeProfile())}
    unknown = set(metrics) - known
    if unknown:
        raise ValueError(f'unknown metrics: {", ".join(sorted(unknown))}')
