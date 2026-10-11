from langgraph.graph import END, START, StateGraph

from .nodes.analyzer import analyzer
from .nodes.architect import architect
from .nodes.clone import clone_repo
from .nodes.coder import coder
from .nodes.planner import planner
from .nodes.publish import docs_writer, pr_creator
from .nodes.review import reviewer, security_checker
from .nodes.testing import fixer, route_after_tests, test_generator, test_runner
from .state import AgentState


def build_graph():
    g = StateGraph(AgentState)
    # NOTE: LangGraph forbids node names that equal a state key, so the security
    # node is called "security_check" (state has a "security" key).
    nodes = [
        ("clone", clone_repo), ("planner", planner), ("analyzer", analyzer),
        ("architect", architect), ("coder", coder), ("test_generator", test_generator),
        ("test_runner", test_runner), ("fixer", fixer), ("reviewer", reviewer),
        ("security_check", security_checker), ("docs", docs_writer), ("pr", pr_creator),
    ]
    for name, fn in nodes:
        g.add_node(name, fn)

    g.add_edge(START, "clone")
    g.add_edge("clone", "planner")
    g.add_edge("planner", "analyzer")
    g.add_edge("analyzer", "architect")
    g.add_edge("architect", "coder")
    g.add_edge("coder", "test_generator")
    g.add_edge("test_generator", "test_runner")
    g.add_conditional_edges("test_runner", route_after_tests, {"fixer": "fixer", "reviewer": "reviewer"})
    g.add_edge("fixer", "test_runner")  # the self-healing loop
    g.add_edge("reviewer", "security_check")
    g.add_edge("security_check", "docs")
    g.add_edge("docs", "pr")
    g.add_edge("pr", END)
    return g.compile()
