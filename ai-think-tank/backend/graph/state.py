from typing import List, Annotated
import operator
from typing_extensions import TypedDict
from models.expert import ExpertProfile, ExpertResponse

def add_responses(left: List[ExpertResponse], right: List[ExpertResponse]) -> List[ExpertResponse]:
    return left + right

class ThinkTankState(TypedDict):
    question: str
    experts: List[ExpertProfile]
    expert_responses: Annotated[List[ExpertResponse], add_responses]
    final_report: str
