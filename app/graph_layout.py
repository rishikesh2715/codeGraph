# import json
# from typing import Dict, Any

# import networkx as nx
# import pydot

# # ---------------------------------------------------------------------------
# # Public API
# # ---------------------------------------------------------------------------

# def layout_graph(flowchart: Dict[str, Any], *, rankdir: str = "TB") -> Dict[str, Any]:
#     """Add absolute x/y coordinates to every node using Graphviz DOT.

#     Parameters
#     ----------
#     flowchart : dict
#         A parsed JSON graph with ``nodes`` and ``edges`` keys – exactly the
#         structure produced by ``llm_graph_generator.generate_graph_from_codebase``.
#     rankdir : str, optional
#         Graph direction. ``'TB'`` = top‑bottom, ``'LR'`` = left‑right, by default
#         "TB".

#     Returns
#     -------
#     dict
#         A *new* dictionary (original unmodified) with ``position`` added to each
#         node::

#             {
#               "id": "train_py",
#               "label": "train.py",
#               "summary": "Orchestrates training loop.",
#               "position": {"x": 123.4, "y": 456.7}
#             }
#     """

#     # ---------------------------------------------------------------------
#     # Build a NetworkX DiGraph from the input JSON
#     # ---------------------------------------------------------------------
#     G = nx.DiGraph()

#     for node in flowchart.get("nodes", []):
#         G.add_node(node["id"], **node)

#     for edge in flowchart.get("edges", []):
#         # Some graphs might contain duplicate edges; networkx will collapse
#         # them, which is fine for our layout purposes.
#         G.add_edge(edge["from"], edge["to"], **edge)

#     # ---------------------------------------------------------------------
#     # Convert to pydot graph and let Graphviz compute positions
#     # ---------------------------------------------------------------------
#     dot_graph: pydot.Dot = nx.nx_pydot.to_pydot(G)  # type: ignore[arg-type]
#     dot_graph.set("rankdir", rankdir)  # enforce directional flow
#     dot_graph.set("nodesep", "0.35")   # tighter spacing
#     dot_graph.set("ranksep", "0.65")   # vertical separation

#     # Request layout from Graphviz (default: dot). For large graphs you might
#     # prefer "sfdp" (force‑directed) or "neato". DOT gives tidy hierarchies.
#     positioned_graphs = pydot.graph_from_dot_data(dot_graph.to_string())
#     if not positioned_graphs:
#         raise RuntimeError("Graphviz returned no graph data.")

#     positioned = positioned_graphs[0]

#     # ---------------------------------------------------------------------
#     # Extract positions back into the node dictionaries
#     # ---------------------------------------------------------------------
#     id_to_pos = {}
#     for n in positioned.get_nodes():
#         raw_id = n.get_name().strip("\"")
#         pos = n.get_pos()
#         if pos is None:
#             continue  # Graphviz may omit isolated nodes; unlikely
#         x_str, y_str = pos.split(",")[:2]
#         id_to_pos[raw_id] = {"x": float(x_str), "y": float(y_str)}

#     # Build the output structure
#     out = json.loads(json.dumps(flowchart))  # deep‑copy
#     for node in out["nodes"]:
#         node_id = node["id"]
#         node["position"] = id_to_pos.get(node_id, {"x": 0.0, "y": 0.0})

#     return out


# # ---------------------------------------------------------------------------
# # Convenience CLI: read graph JSON ➜ emit positioned JSON
# # ---------------------------------------------------------------------------
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) != 3:
#         print("Usage: python -m app.graph_layout in.json out.json", file=sys.stderr)
#         sys.exit(1)

#     with open(sys.argv[1], "r", encoding="utf-8") as fh:
#         raw = json.load(fh)
#     laid_out = layout_graph(raw)
#     with open(sys.argv[2], "w", encoding="utf-8") as fh:
#         json.dump(laid_out, fh, indent=2)
#     print(f"✓ Wrote laid‑out graph to {sys.argv[2]}")


import json
from typing import Dict, Any
import networkx as nx

def layout_graph(flowchart: Dict[str, Any], *, rankdir: str = "TB") -> Dict[str, Any]:
    G = nx.DiGraph()
    for node in flowchart.get("nodes", []):
        G.add_node(node["id"], **node)
    for edge in flowchart.get("edges", []):
        G.add_edge(edge["from"], edge["to"], **edge)

    # tell graphviz about spacing + direction
    G.graph["graph"] = {"rankdir": rankdir, "nodesep": "0.35", "ranksep": "0.65"}

    # --- run Graphviz to get coordinates ---
    try:
        # requires: system graphviz installed (dot), and `pip install pydot`
        pos = nx.nx_pydot.graphviz_layout(G, prog="dot")
    except Exception:
        # fallback so you still see something if dot isn't available
        pos = nx.spring_layout(G, seed=42)

    out = json.loads(json.dumps(flowchart))  # deep copy
    for node in out["nodes"]:
        p = pos.get(node["id"])
        node["position"] = {"x": float(p[0]), "y": float(p[1])} if p is not None else {"x": 0.0, "y": 0.0}
    return out
