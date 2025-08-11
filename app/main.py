from flask import Flask, render_template, request, jsonify
import os
import json
import fnmatch

from .llm_graph_generator import generate_graph_from_codebase
from .graph_layout        import layout_graph          # NEW ⭐

app = Flask(__name__, template_folder='../templates', static_folder='../static')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json() or {}
    use_mock = bool(data.get('use_mock', False))
    mock_filename = data.get('mock_filename', 'mock_graph.json')

    raw_graph = None

    if use_mock:
        # Load from /static/<mock_filename>
        mock_path = os.path.join(app.static_folder, mock_filename)
        if not os.path.isfile(mock_path):
            return jsonify({"error": f"Mock file not found: {mock_path}"}), 400
        try:
            with open(mock_path, "r", encoding="utf-8") as fh:
                raw_graph = json.load(fh)
        except Exception as exc:
            return jsonify({"error": f"Failed to read mock JSON: {exc}"}), 400
    else:
        # Original path-based analysis (LLM)
        if 'path' not in data:
            return jsonify({"error": "Request must be JSON with a 'path' key (or set use_mock=true)."}), 400

        project_root = data['path']
        if not os.path.isdir(project_root):
            return jsonify({"error": "Path does not exist or is not a directory."}), 400

        EXCLUDE_DIRS = {
            "venv", ".venv", "env",
            "__pycache__", ".git", ".hg",
            ".idea", ".vscode", "node_modules",
            ".mypy_cache", ".pytest_cache"
        }

        def should_skip_dir(dirname: str) -> bool:
            return dirname in EXCLUDE_DIRS or "site-packages" in dirname

        file_contents = {}
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]
            for file in files:
                if not fnmatch.fnmatch(file, "*.py"):
                    continue
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        file_contents[file_path] = f.read()
                except UnicodeDecodeError:
                    print(f"⚠️  Skipped non-UTF8 file {file_path}")
                except Exception as e:
                    print(f"⚠️  Could not read {file_path}: {e}")

        raw_graph = generate_graph_from_codebase(file_contents)

    if not raw_graph:
        return jsonify({"error": "Failed to get graph data."}), 500

    graph = layout_graph(raw_graph, rankdir="TB")

    # Mermaid string + summaries + edge details (unchanged)
    mermaid_def   = "graph TB;\n"
    summaries     = {}
    edge_details  = {}

    for node in graph['nodes']:
        node_id    = node['id'].replace('-', '_')
        node_label = node['label']
        mermaid_def += f'    {node_id}["{node_label}"];\n'
        summaries[node_id] = node['summary']

    for edge in graph['edges']:
        from_node  = edge['from'].replace('-', '_')
        to_node    = edge['to'].replace('-', '_')
        label      = edge['label'].replace('"', "'")
        mermaid_def += f'    {from_node} -- "{label}" --> {to_node};\n'

        edge_id = f"{from_node}_{to_node}"
        edge_details.setdefault(edge_id, []).append({
            "from": from_node,
            "to"  : to_node,
            "snippet": label
        })

    return jsonify({
        "mermaid"     : mermaid_def,
        "summaries"   : summaries,
        "edge_details": edge_details,
        "graph"       : graph
    })



if __name__ == '__main__':
    app.run(debug=True, port=5001)
