import os
import re
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.prompts import PromptTemplate
from utils.langchain_utils import get_agent_with_prompt
from utils.models import (
    CodeRequest,
    FeedbackRequest,
    ImproveCodeRequest,
    RunTestRequest,
    TestRequest,
)
from utils.prompts import (
    PromptInjectionDetector,
    feedback_prompt,
    generate_prompt,
    generate_tests_prompt,
    improve_code_based_on_tests_prompt,
    improve_tests_prompt,
)
from utils.safety_utils import evaluate_code
from utils.utils import get_code_from_response

app = FastAPI()

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# In-memory storage for snippets
snippets = {}


detector = PromptInjectionDetector()


@tool
def is_prompt_injection_attack(text: str) -> bool:
    """
    Returns True if the text contains a prompt injection attack, False otherwise.
    """
    return detector.is_prompt_injection_attack(text)


# Initialize LangChain OpenAI model
llm = ChatOpenAI(model="gpt-3.5-turbo")
tools = [is_prompt_injection_attack]


# Endpoints
@app.post("/generate_code/")
async def generate_code(request: CodeRequest):
    prompt = generate_prompt(request.language)
    agent = get_agent_with_prompt(prompt=prompt, llm=llm, tools=tools)

    response = agent.invoke(
        {
            "input": f"Code snippet language: {request.language}\nCode snippet description: {request.description}"
        }
    )["output"]
    
    print(f"Response: {response}")

    code = get_code_from_response(response)
    snippet_id = str(uuid.uuid4())
    snippets[snippet_id] = {
        "description": request.description,
        "language": request.language,
        "code": code,
    }
    return {"id": snippet_id, "code": code}


@app.post("/provide_feedback/")
async def provide_feedback(request: FeedbackRequest):
    prompt = feedback_prompt(request.language)

    agent = get_agent_with_prompt(prompt=prompt, llm=llm, tools=tools)
    response = agent.invoke(
        {
            "input": f"Code snippet language: {request.language}\nCode snippet description: {request.code}\nFeedback: {request.feedback}"
        }
    )["output"]
    print(f"Response: {response}")
    improved_code = get_code_from_response(response)
    return {"code": improved_code}


@app.post("/generate_tests/")
async def generate_tests(request: TestRequest):
    prompt = generate_tests_prompt()

    agent = get_agent_with_prompt(prompt=prompt, llm=llm, tools=tools)
    
    response = agent.invoke(
        {
            "input": f"Code snippet language: {request.language}\nCode snippet description: {request.code}"
        }
    )["output"]
    tests = get_code_from_response(response)
    
    print(f"Response: {response}")
    snippet_id = str(uuid.uuid4())
    snippets.setdefault(snippet_id, {})
    snippets[snippet_id]["tests"] = tests
    return {"id": snippet_id, "tests": tests}


@app.post("/provide_test_feedback/")
async def provide_test_feedback(request: FeedbackRequest):
    prompt = improve_tests_prompt()
    agent = get_agent_with_prompt(prompt=prompt, llm=llm, tools=tools)
    response = agent.invoke(
        {
            "input": f"Code snippet language: {request.language}\nCode snippet description: {request.code}\nFeedback: {request.feedback}"
        }
    )["output"]
    
    print(f"Response: {response}")
    improved_tests = get_code_from_response(response)
    return {"tests": improved_tests}


@app.post("/run_tests/")
async def run_tests(request: RunTestRequest):
    if request.language.lower() == "python":
        try:
            result = evaluate_code(request.code + "\n" + request.tests)
            return {"results": result, "success": True}
        except Exception as e:
            return {"results": str(e), "success": False}
    else:
        return {
            "results": "Running tests is only supported for Python.",
            "success": False,
        }


@app.post("/improve_code_based_on_tests/")
async def improve_code_based_on_tests(request: ImproveCodeRequest):
    prompt = improve_code_based_on_tests_prompt(request.code, request.testResults)
    response = llm(prompt)
    improved_code = response.strip()
    return {"code": improved_code}


@app.get("/snippets/")
async def get_snippets():
    return {"snippets": [{"id": id, **data} for id, data in snippets.items()]}


@app.delete("/snippets/{snippet_id}")
async def delete_snippet(snippet_id: str):
    if snippet_id in snippets:
        del snippets[snippet_id]
    return {"message": "Snippet deleted successfully"}


@app.get("/")
async def read_root():
    return FileResponse("pages/design.html")
