from llama_index.core.tools import FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent import ReActAgent
from llama_index.core.llms import ChatMessage


def calculate_mortgage_payment(principal, annual_rate, years, payment_frequency):
    """
    Calculate the periodic mortgage payment.

    :param principal: The principal loan amount (in dollars).
    :param annual_rate: The annual interest rate (as a decimal, e.g., 0.05 for 5%).
    :param years: The loan term in years.
    :param payment_frequency: Number of payments per year (e.g., 12 for monthly, 26 for bi-weekly).
    :return: The periodic payment amount.
    """
    # Convert annual rate to periodic rate
    periodic_rate = annual_rate / payment_frequency
    
    # Total number of payments
    total_payments = years * payment_frequency
    
    # Calculate the periodic payment
    payment = principal * (periodic_rate * (1 + periodic_rate)**total_payments) / ((1 + periodic_rate)**total_payments - 1)
    
    return payment

mort_payment_tool = FunctionTool.from_defaults(fn=calculate_mortgage_payment)

def calculate_total_interest(principal, annual_rate, years, payment_frequency, year_n):
    """
    Calculate the total interest paid by the end of year n.

    :param principal: The principal loan amount (in dollars).
    :param annual_rate: The annual interest rate (as a decimal, e.g., 0.05 for 5%).
    :param years: The loan term in years.
    :param payment_frequency: Number of payments per year (e.g., 12 for monthly, 26 for bi-weekly).
    :param year_n: The specific year to calculate total interest paid by.
    :return: The total interest paid by the end of year n.
    """
    # Calculate the periodic payment
    periodic_payment = calculate_mortgage_payment(principal, annual_rate, years, payment_frequency)
    
    # Convert annual rate to periodic rate
    periodic_rate = annual_rate / payment_frequency
    
    # Total number of payments up to year_n
    total_payments_n = year_n * payment_frequency
    
    # Total amount paid up to year_n
    total_paid_n = periodic_payment * total_payments_n
    
    # Calculate remaining balance after year_n
    remaining_balance = principal * ((1 + periodic_rate)**(years * payment_frequency) - (1 + periodic_rate)**total_payments_n) / ((1 + periodic_rate)**(years * payment_frequency) - 1)
    
    # Total interest paid by year_n
    total_interest_paid = total_paid_n - (principal - remaining_balance)
    
    return total_interest_paid

mort_interest_tool = FunctionTool.from_defaults(fn=calculate_total_interest)


# initialize llm
llm = OpenAI(api_base="http://localhost:1234/v1", api_key="lm-studio", model="gpt-3.5-turbo-0613")

# initialize ReAct agent
agent = ReActAgent.from_tools([mort_payment_tool,mort_interest_tool], llm=llm, verbose=True,max_iterations = 50)

response = agent.chat("If I have a 27 year loan of $500,000 on 5.89% interest and fortnightly payments, what is the total interest I will pay after the first 5 years of my loan? Think it through step by step.")

