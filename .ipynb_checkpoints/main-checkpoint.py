from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage
from src.utils import generate_python_function, partition_by_tool, write_to_file, list_functions_in_file, get_function_by_name



# initialize llm
llm = OpenAI(api_base="http://localhost:1234/v1", api_key="lm-studio", model="gpt-3.5-turbo-0613",timeout=500)

query = "I have a mortgage of $735,000 and I have 27 years left on my loan. My interest rate is 6.14% per year. If I pay $1000 extra per fortnight on top of my regular fortnightly repayments, how long will it take me to pay off my loan?"

tool_creator_sys_prompt = """
You are a tool creator. You will be given a query by the user. Please list the tools required (custom python functions) in order to complete this query, and include a detailed description of each tool with inputs and returns compliant with PEP8 style guide. DO NOT USE ANY SPECIAL CHARACTERS LIKE **. DO NOT WRITE THE ACTUAL PYTHON CODE. Think it through step by step.

## Output Format

Tool 1: Description of tool

Tool 2: Description of tool

etc
"""
messages = [
    ChatMessage(role="system", content = tool_creator_sys_prompt),
    ChatMessage(role="user", content=query)
]
resp = llm.chat(messages).message.content

for item in partition_by_tool(resp):
    write_to_file(generate_python_function(item),'src/tools.py')
    

my_tools = list_functions_in_file('src/tools.py')

from src.tools import *

agent = ReActAgent.from_tools([FunctionTool.from_defaults(fn=globals().get(tool)) for tool in my_tools], llm=llm, verbose=True,max_iterations = 50)

agent.chat(query)