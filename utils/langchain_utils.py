from typing import List
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import (
    SystemMessagePromptTemplate,
    PromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    ChatPromptTemplate,
)


def get_agent_with_prompt(
    llm: ChatOpenAI, tools: List[Tool], prompt: str
) -> AgentExecutor:
    messages = [
        SystemMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=[], template=prompt)
        ),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        HumanMessagePromptTemplate(
            prompt=PromptTemplate(input_variables=["input"], template="{input}")
        ),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]

    agent_prompt = ChatPromptTemplate.from_messages(messages)
    agent = create_tool_calling_agent(llm, tools, agent_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)
    return agent_executor
