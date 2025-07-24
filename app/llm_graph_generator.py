import os
import google.generativeai as genai
import json

# Configure the Gemini API key
try:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError:
    raise EnvironmentError("GEMINI_API_KEY environment variable not set.")

# Initialize the Generative Model
model = genai.GenerativeModel('gemini-2.5-pro')

def generate_graph_from_codebase(file_contents):
    """
    Uses the LLM to analyze a whole codebase and generate a graph in JSON format.
    """
    system_prompt = """
You are an expert software architect. Your task is to analyze a given codebase, provided as a collection of files, and generate a high-level flowchart that explains its structure and logic.

Analyze the provided files and identify the key components, modules, or concepts. These will be the nodes of your graph.
Then, determine the relationships and dependencies between these components. These will be the arrows (edges) of your graph. The relationships should be more descriptive than simple imports; think about data flow, function calls, or logical sequence.

You MUST return your analysis in a single, valid JSON object. Do not include any text or formatting before or after the JSON object.
The JSON object must have two keys: "nodes" and "edges".

1.  **nodes**: An array of objects, where each object represents a block in the flowchart. Each node object must have:
    *   `id`: A short, unique, snake_case identifier for the node (e.g., "data_loader", "model_trainer").
    *   `label`: A human-readable name for the block (e.g., "Data Loader", "Model Trainer").
    *   `summary`: A concise, one-sentence explanation of what this component does.

2.  **edges**: An array of objects, where each object represents an arrow connecting two blocks. Each edge object must have:
    *   `from`: The `id` of the source node.
    *   `to`: The `id` of the target node.
    *   `label`: A brief description of the relationship (e.g., "sends preprocessed data to", "calls training function", "imports configuration from").

Example Output Structure:
```json
{
  "nodes": [
    {
      "id": "config_parser",
      "label": "Configuration Parser",
      "summary": "Reads and validates the main configuration file for the application."
    },
    {
      "id": "main_app",
      "label": "Main Application",
      "summary": "Initializes the application and orchestrates the main workflow."
    }
  ],
  "edges": [
    {
      "from": "main_app",
      "to": "config_parser",
      "label": "loads settings from"
    }
  ]
}
```
"""

    user_prompt = "Here is the codebase. Please generate the flowchart JSON for it:\n\n"
    
    # Combine all file contents into a single string for the prompt
    for path, content in file_contents.items():
        # Use a relative path for cleaner presentation to the LLM
        relative_path = os.path.relpath(path, start=os.path.dirname(list(file_contents.keys())[0]))
        user_prompt += f"--- File: {relative_path} ---\n"
        user_prompt += f"```python\n{content}\n```\n\n"

    try:
        full_prompt = [system_prompt, user_prompt]
        response = model.generate_content(full_prompt)
        
        # Clean up the response to extract only the JSON part
        cleaned_response = response.text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]
        
        return json.loads(cleaned_response)
        
    except Exception as e:
        print(f"Error generating graph from LLM: {e}")
        # Also print the response text if available, for debugging
        if 'response' in locals() and hasattr(response, 'text'):
            print("LLM Response Text:", response.text)
        return None
