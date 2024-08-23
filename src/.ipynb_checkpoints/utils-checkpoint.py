from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
import re
import ast

def list_functions_in_file(file_name: str) -> list:
    """
    Lists all the function names defined in a given Python file.

    Parameters:
        file_name (str): The name of the Python file to analyze.

    Returns:
        list: A list of function names defined in the file.
    """
    function_names = []
    
    try:
        with open(file_name, "r") as file:
            file_content = file.read()
        
        # Parse the file content into an Abstract Syntax Tree (AST)
        parsed_content = ast.parse(file_content)
        
        # Iterate through the AST nodes and find function definitions
        for node in ast.walk(parsed_content):
            if isinstance(node, ast.FunctionDef):
                function_names.append(node.name)
        
        return function_names
    
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


def generate_python_function(request: str) -> str:
    """
    Generates a Python function based on a given request using an LLM.

    Parameters:
    request (str): The request describing the desired function.

    Returns:
    str: The generated Python function as a string.
    """
    
    try:
        my_llm = OpenAI(api_base="http://localhost:1234/v1", api_key="lm-studio", model="gpt-3.5-turbo-0613")
        messages = [
            ChatMessage(
            role="system", content="You are an expert Python software engineer. You write efficient python functions.\n\n\n## Output Format\n\nYou will respond with only the requested python function. NEVER surround your response with markdown code markers. Make sure it complies with PEP8 style guide. Include a text description of what the function does, inputs and returns within the function."
                        ),
            ChatMessage(role="user", content=request),
]
        resp = my_llm.chat(messages)
        return resp.message.content
    except Exception as e:
        return f"An error occurred: {str(e)}"
    


def partition_by_tool(string):
    # Regular expression pattern to match "Tool n:" where n is an integer
    pattern = r"(Tool \d+:)"
    
    # Find all the matches for the pattern
    matches = re.findall(pattern, string)
    
    # If no matches found, return the entire string as a single element list
    if not matches:
        return [string]
    
    # Split the string based on the pattern, while keeping the delimiter
    parts = re.split(pattern, string)
    
    # Combine the split parts with their corresponding "Tool n:" identifiers
    partitioned_list = []
    for i in range(len(parts)):
        if parts[i].startswith("Tool"):
            # Skip adding the "Tool n:" part and add the following text
            partitioned_list.append(parts[i+1].strip())
        elif not parts[i].startswith("Tool"):
            continue
    
    return partitioned_list

def write_to_file(content: str, file_name: str, overwrite: bool = False) -> None:
    """
    Writes the given content to a file.

    Parameters:
        content (str): The content to write to the file.
        file_name (str): The name of the file.
        overwrite (bool): Flag to determine if the file should be overwritten.
                          If False, the content will be appended to the file.
                          Default is False (append mode).
    """
    mode = 'w' if overwrite else 'a'
    try:
        with open(file_name, mode) as file:
            file.write(content)
            file.write('\n')  # Optional: Adds a newline after the content
        print(f"Content {'overwritten' if overwrite else 'appended'} to {file_name}")
    except Exception as e:
        print(f"An error occurred: {e}")
