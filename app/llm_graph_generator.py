import os
import re
import json
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Gemini setup
# ---------------------------------------------------------------------------
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    raise EnvironmentError("GEMINI_API_KEY environment variable not set.")

model = genai.GenerativeModel("gemini-2.5-pro")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _guess_lang(path: str) -> str:
    """
    Return a language tag for markdown code-fences based on file extension.
    Keeps the LLM in the right “mode” for syntax highlighting.
    """
    ext = os.path.splitext(path)[1].lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
    }.get(ext, "")  # default: no language hint


def _to_snake(name: str) -> str:
    """
    Converts any string to snake_case (used only in the instructions; the LLM will obey).
    """
    name = re.sub(r"\W+", "_", name)          # replace non-word chars
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)  # CamelCase → snake
    return name.lower().strip("_")


# ---------------------------------------------------------------------------
# Core function
# ---------------------------------------------------------------------------
def generate_graph_from_codebase(file_contents: dict[str, str]) -> dict | None:
    """
    Analyse a whole codebase and return a flowchart description as JSON.

    Parameters
    ----------
    file_contents : dict
        Mapping absolute/relative file path ➜ file text.

    Returns
    -------
    dict | None
        Parsed JSON with 'nodes' and 'edges' or None on failure.
    """

    # ---------- System prompt ------------------------------------------------
    system_prompt = """
You are an expert software architect. Your task is to analyse a given codebase
and generate a high-level flowchart that explains its structure and logic.

Analyse the provided files and identify the key components or modules—these will
be the nodes. Then determine relationships and dependencies—these will be the
edges. Think beyond mere imports: consider data flow, function calls, or logical
sequence.

Return ONE valid JSON object containing exactly two keys: "nodes" and "edges".
Do NOT output anything before or after the JSON.

•  For EVERY file you receive, create exactly ONE node.
•  `id` MUST be the file’s base-name in snake_case **without** the extension.
•  `label` MUST be the original file name **with** extension.

nodes: [
  { id, label, summary }            # summary = one concise sentence
]

edges: [
  { from, to, label }               # label ≈ “calls”, “imports”, “sends data to”…
]
"""

    # ---------- User prompt --------------------------------------------------
    manifest = "\n".join(sorted(os.path.basename(p) for p in file_contents))
    user_prompt = (
        f"Here is the codebase ({len(file_contents)} files).\n"
        f"File manifest (for reference):\n{manifest}\n\n"
        "Please generate the flowchart JSON for it:\n\n"
    )

    # Embed each file with a language-aware code fence
    root_dir = os.path.dirname(os.path.commonprefix(list(file_contents.keys())))
    for path, content in file_contents.items():
        rel_path = os.path.relpath(path, start=root_dir)
        lang = _guess_lang(path)
        user_prompt += f"--- File: {rel_path} ---\n"
        user_prompt += f"```{lang}\n{content}\n```\n\n"

    # ---------- LLM call -----------------------------------------------------
    try:
        response = model.generate_content([system_prompt, user_prompt])
        cleaned = response.text.strip()

        # Strip ```json fences if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        return json.loads(cleaned)

    except Exception as exc:
        print(f"[ERROR] generate_graph_from_codebase: {exc}")
        if "response" in locals() and hasattr(response, "text"):
            print("LLM raw response:\n", response.text)
        return None
