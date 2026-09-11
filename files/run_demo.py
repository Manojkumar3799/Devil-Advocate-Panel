"""
Standalone CLI demo of the panel graph -- no Streamlit yet.
Run: python -m devils_advocate.run_demo

Requires GROK_API_KEY (xai), GOOGLE_API_KEY, GROQ_API_KEY, TAVILY_API_KEY
in a .env file (see .env.example) for the fallback chain / tools to work.
"""

from dotenv import load_dotenv
from langgraph.types import Command

from .graph import build_graph
from .state import initial_state

load_dotenv()


def main():
    graph = build_graph()
    thread_id = "demo-session-1"
    config = {"configurable": {"thread_id": thread_id}}

    pitch = input("Pitch your idea:\n> ")
    intensity = input("Intensity [light/normal/heavy/no_mercy]: ").strip() or "normal"
    connected = []  # no OAuth connectors wired up yet in this standalone demo

    state = initial_state(pitch, intensity, connected)
    result = graph.invoke(state, config=config)

    # Loop: whenever the graph hits an interrupt, print the question,
    # take the founder's reply, and resume the same thread.
    while "__interrupt__" in result:
        interrupt_payload = result["__interrupt__"][0].value
        print(f"\n[{interrupt_payload['persona'].upper()}]: {interrupt_payload['question']}\n")
        reply = input("Your response: ")
        result = graph.invoke(Command(resume=reply), config=config)

    print("\n=== VERDICT ===")
    for w in result.get("verdict", []):
        print(f"[severity {w['severity']}] {w['issue']}\n  fix: {w['fix']}\n")


if __name__ == "__main__":
    main()
