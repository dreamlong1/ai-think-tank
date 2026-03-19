from pydantic import BaseModel
from typing import List, Optional

class QuestionRequest(BaseModel):
    question: str

class SummaryResponse(BaseModel):
    consensus: str
    disagreements: str
    blind_spots: str
    conclusion: str
