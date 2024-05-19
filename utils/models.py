from pydantic import BaseModel


class CodeRequest(BaseModel):
    description: str
    language: str


class FeedbackRequest(BaseModel):
    code: str
    feedback: str
    language: str


class TestRequest(BaseModel):
    code: str
    language: str


class RunTestRequest(BaseModel):
    code: str
    tests: str
    language: str


class ImproveCodeRequest(BaseModel):
    code: str
    testResults: str
