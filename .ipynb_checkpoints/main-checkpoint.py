from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
from src.utils import generate_python_function, partition_by_tool, write_to_file, list_functions_in_file



# initialize llm
llm = OpenAI(api_base="http://localhost:1234/v1", api_key="lm-studio", model="gpt-3.5-turbo-0613")

tool_creator_sys_prompt = """
You are a tool creator. You will be given a query by the user. Please list the tools required (custom python functions) in order to complete this query, and include a detailed description of each tool with inputs and returns compliant with PEP8 style guide. DO NOT USE ANY SPECIAL CHARACTERS LIKE **. DO NOT WRITE THE ACTUAL PYTHON CODE. Think it through step by step.

## Output Format

Tool 1: Description of tool

Tool 2: Description of tool

etc
"""
messages = [
    ChatMessage(role="system", content = tool_creator_sys_prompt),
    ChatMessage(role="user", content="I want to do full scenario planning for my mortgage, including plotting my interest over time, calculating savings, budgeting etc. EVERYTHING. Please think of other things I may want to calculate and include them in your scope. It needs to be a complete solution for all mortgage related enquiries.")
]
resp = llm.chat(messages).message.content

my_functions = []

for item in partition_by_tool(resp):
    write_to_file(generate_python_function(item),'src/tools.py')
    

