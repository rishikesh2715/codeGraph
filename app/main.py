from flask import Flask, render_template, request, jsonify
import os
import json
from .llm_graph_generator import generate_graph_from_codebase

app = Flask(__name__, template_folder='../templates', static_folder='../static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({"error": "Request must be JSON with a 'path' key."}), 400

    folder_path = data.get('path')

    if not folder_path or not os.path.isdir(folder_path):
        return jsonify({"error": "Invalid or missing folder path"}), 400

    file_contents = {}
    excluded_dirs = {'.git', 'venv', '.venv', '__pycache__', 'dist', 'build', 'node_modules', '.vscode'}
    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        file_contents[file_path] = f.read()
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")
    
    if not file_contents:
        return jsonify({"error": "No Python files found in the specified directory."}), 400

    # Use the new LLM-based generator
    graph_data = generate_graph_from_codebase(file_contents)
    
    if not graph_data:
        return jsonify({"error": "Failed to generate graph from LLM. The model may have returned an invalid format."}), 500

    # Build Mermaid definition and other frontend data from the LLM response
    mermaid_def = "graph TD;\n"
    summaries = {}
    edge_details = {}

    for node in graph_data.get('nodes', []):
        # Ensure IDs are valid for Mermaid
        node_id = str(node.get('id', '')).replace('-', '_')
        node_label = node.get('label', 'Unnamed Node')
        mermaid_def += f'    {node_id}["{node_label}"];\n'
        summaries[node_id] = node.get('summary', 'No summary provided.')

    for edge in graph_data.get('edges', []):
        from_node = str(edge.get('from', '')).replace('-', '_')
        to_node = str(edge.get('to', '')).replace('-', '_')
        edge_label = edge.get('label', '').replace('"', "'") # Sanitize quotes
        
        if from_node and to_node:
            mermaid_def += f'    {from_node} -- "{edge_label}" --> {to_node};\n'
            
            # The tooltip will now show the LLM's description of the edge
            edge_id = f"{from_node}_{to_node}"
            if edge_id not in edge_details:
                edge_details[edge_id] = []

            edge_details[edge_id].append({
                "from": from_node,
                "to": to_node,
                "snippet": edge_label
            })

    final_response = {
        "mermaid": mermaid_def,
        "summaries": summaries,
        "edge_details": edge_details
    }
    
    return jsonify(final_response)

if __name__ == '__main__':
    app.run(debug=True, port=5001)