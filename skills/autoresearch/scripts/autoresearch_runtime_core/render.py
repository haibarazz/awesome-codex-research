"""Render the canonical experiment graph into a self-contained HTML view."""

from __future__ import annotations

import html
import json
from collections import defaultdict, deque
from typing import Any


def _depths(graph: dict[str, Any]) -> dict[str, int]:
    nodes = {node["node_id"] for node in graph["nodes"]}
    incoming: dict[str, list[str]] = defaultdict(list)
    outgoing: dict[str, list[str]] = defaultdict(list)
    for edge in graph["edges"]:
        if edge["edge_type"] == "PRIMARY_PARENT":
            incoming[edge["to_node_id"]].append(edge["from_node_id"])
            outgoing[edge["from_node_id"]].append(edge["to_node_id"])
        elif edge["edge_type"] == "DIRECTION":
            incoming[edge["to_node_id"]].append(edge["from_node_id"])
            outgoing[edge["from_node_id"]].append(edge["to_node_id"])
    depth = {node_id: 0 for node_id in nodes if not incoming[node_id]}
    queue = deque(sorted(depth))
    while queue:
        parent = queue.popleft()
        for child in sorted(outgoing[parent]):
            next_depth = depth[parent] + 1
            if next_depth > depth.get(child, -1):
                depth[child] = next_depth
                queue.append(child)
    return {node_id: depth.get(node_id, 0) for node_id in nodes}


def render_graph_html(graph: dict[str, Any]) -> str:
    depths = _depths(graph)
    columns: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for node in graph["nodes"]:
        columns[depths[node["node_id"]]].append(node)

    role_state = graph["role_states"][graph["active_benchmark_id"]]
    roles: dict[str, list[str]] = defaultdict(list)
    roles[role_state["anchor_baseline_id"]].append("Anchor")
    roles[role_state["research_base_id"]].append("Research Base")
    roles[role_state["champion_id"]].append("Champion")
    for node_id in role_state["reference_baseline_ids"]:
        roles[node_id].append("Reference")

    frontier = set(graph["active_frontier"])
    cards: list[str] = []
    for depth in sorted(columns):
        rendered_nodes: list[str] = []
        for node in sorted(columns[depth], key=lambda item: item["node_id"]):
            node_id = node["node_id"]
            badges = [
                f'<span class="badge role">{html.escape(role)}</span>'
                for role in roles.get(node_id, [])
            ]
            if node_id in frontier:
                badges.append('<span class="badge frontier">Frontier</span>')
            if node["node_type"] == "RESEARCH":
                status = (
                    f'{node["branch_status"]} · {node["run_outcome"]} · '
                    f'{node["hypothesis_verdict"]}'
                )
                metric = " · ".join(
                    f'{item["label"]}: {item["value"]}'
                    for item in node["metric_summary"]
                    if item["value"] is not None
                )
                detail = node["single_main_change"] or "Baseline root"
            else:
                status = node["search_outcome"]
                metric = ""
                detail = node["direction_summary"] or node["outcome_reason"]
            rendered_nodes.append(
                "\n".join(
                    [
                        f'<article class="node {node["node_type"].lower()}">',
                        f'<div class="node-id">{html.escape(node_id)}</div>',
                        f"<h3>{html.escape(node['title'])}</h3>",
                        f'<div class="badges">{"".join(badges)}</div>',
                        f'<p class="detail">{html.escape(detail or "")}</p>',
                        f'<p class="status">{html.escape(status)}</p>',
                        f'<p class="metric">{html.escape(metric)}</p>',
                        "</article>",
                    ]
                )
            )
        cards.append(
            f'<section class="column"><div class="column-label">Depth {depth}</div>'
            f'{"".join(rendered_nodes)}</section>'
        )

    embedded = json.dumps(graph, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(graph["project_id"])} · Experiment Graph</title>
  <style>
    :root {{ --cream:#fbf4df; --paper:#fffdf7; --ink:#443b35; --line:#d9c9a7;
      --peach:#efaa83; --mint:#9fc9b5; --blue:#9dbfd4; --shadow:#9f8d7140; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--ink); background:
      radial-gradient(circle at 12% 8%, #fff9e9 0 7%, transparent 8%),
      linear-gradient(135deg, var(--cream), #f7ead3); font:15px/1.45 ui-rounded,
      "SF Pro Rounded", system-ui, sans-serif; min-height:100vh; }}
    header {{ position:sticky; left:0; top:0; z-index:3; padding:20px 28px;
      background:#fff9edee; border-bottom:2px dashed var(--line); backdrop-filter:blur(8px); }}
    h1 {{ margin:0; font-size:25px; }} header p {{ margin:5px 0 0; color:#75685c; }}
    .graph {{ display:flex; align-items:flex-start; gap:28px; padding:28px;
      min-width:max-content; overflow-x:auto; }}
    .column {{ width:290px; display:flex; flex-direction:column; gap:18px; }}
    .column-label {{ font-weight:800; color:#87745d; padding-left:4px; }}
    .node {{ position:relative; padding:18px; background:var(--paper); border:2px solid var(--line);
      border-radius:22px 16px 24px 14px; box-shadow:6px 7px 0 var(--shadow); }}
    .node::after {{ content:"→"; position:absolute; right:-24px; top:44%; color:#a98d69;
      font-size:22px; font-weight:900; }}
    .column:last-child .node::after {{ display:none; }}
    .node.literature {{ border-color:var(--blue); }}
    .node-id {{ font:700 12px/1.2 ui-monospace, monospace; color:#887a6b; }}
    h3 {{ margin:7px 0 10px; font-size:18px; }}
    .badges {{ min-height:24px; display:flex; flex-wrap:wrap; gap:5px; }}
    .badge {{ display:inline-block; padding:3px 8px; border-radius:99px; font-size:11px;
      font-weight:800; background:#eee2c9; }}
    .badge.role {{ background:#f7cbb2; }} .badge.frontier {{ background:#bfe3cf; }}
    .detail {{ margin:12px 0 8px; }} .status {{ margin:0; color:#7b6855; font-size:12px; }}
    .metric {{ min-height:18px; margin:8px 0 0; font-weight:800; color:#4d7464; }}
  </style>
</head>
<body>
  <header>
    <h1>🧪 {html.escape(graph["project_id"])}</h1>
    <p>Revision {graph["revision"]} · Benchmark {html.escape(graph["active_benchmark_id"])}
      · Updated {html.escape(graph["updated_at"])}</p>
  </header>
  <main class="graph">{"".join(cards)}</main>
  <script id="experiment-graph" type="application/json">{embedded}</script>
</body>
</html>
"""
