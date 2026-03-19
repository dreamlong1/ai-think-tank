from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from graph.state import ThinkTankState
from graph.nodes.coordinator import coordinator_node
from graph.nodes.expert import expert_node, ExpertSubState
from graph.nodes.synthesizer import synthesizer_node

def continue_to_experts(state: ThinkTankState):
    # 这里使用 `Send` API 为每位专家动态生成一条并行分支。
    # 返回的 Send 列表会让 `expert_node` 同时执行。
    question = state["question"]
    experts = state["experts"]
    
    # 每个分支都带上问题和专家画像。
    # 这里优先转成 dict，保证序列化和传输更稳定。
    return [
        Send("expert_node", {
            "question": question,
            "expert_profile": expert.model_dump() if hasattr(expert, "model_dump") else expert
        })
        for expert in experts
    ]

# 构建图
builder = StateGraph(ThinkTankState)

builder.add_node("coordinator_node", coordinator_node)
builder.add_node("expert_node", expert_node)
builder.add_node("synthesizer_node", synthesizer_node)

builder.add_edge(START, "coordinator_node")

# 协调节点结束后，分发到多个专家节点
builder.add_conditional_edges("coordinator_node", continue_to_experts, ["expert_node"])

# 专家节点结束后进入总结节点，`expert_responses` 会在这里汇总
builder.add_edge("expert_node", "synthesizer_node")
builder.add_edge("synthesizer_node", END)

# 编译图
graph_app = builder.compile()
