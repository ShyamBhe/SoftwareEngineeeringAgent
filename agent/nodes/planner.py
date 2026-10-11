from .. import llm

SYSTEM = """You are a senior software engineer planning a change to an existing repo.
Produce JSON: {"goal": str, "steps": [str], "risks": [str],
"needs_new_dependencies": [str], "acceptance_criteria": [str]}"""


def planner(state):
    plan = llm.ask_json(SYSTEM, f"Task: {state['task']}")
    return {"plan": plan, "events": state["events"] + [f"Plan: {len(plan['steps'])} steps"]}
