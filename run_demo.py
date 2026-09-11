"""
Standalone CLI runner for the Devil's Advocate Panel graph.
Tests the core loop and interrupt/resume cycle headlessly.

Usage:
    python run_demo.py
"""

from __future__ import annotations

import sys
from dotenv import load_dotenv
from langgraph.types import Command

from core.graph import build_graph
from core.state import initial_state

load_dotenv()


def main():
    print("=" * 60)
    print("🔥 DEVIL'S ADVOCATE PANEL — CLI DEMO 🔥")
    print("=" * 60)
    print("Pitch your idea. Get grilled by AI investors.\n")

    pitch = input("Enter your pitch:\n> ").strip()
    if not pitch:
        pitch = "We are building an AI-powered dog walking scheduling SaaS for enterprise office buildings with $10k MRR."
        print(f"Defaulting to pitch: '{pitch}'")

    intensity = input("\nIntensity [light, normal, heavy, no_mercy] (default: normal): ").strip().lower()
    if intensity not in ("light", "normal", "heavy", "no_mercy"):
        intensity = "normal"

    print(f"\nInitializing panel with intensity: [{intensity}]...")
    graph = build_graph()
    thread_id = "cli-demo-session-1"
    config = {"configurable": {"thread_id": thread_id}}

    state = initial_state(pitch_text=pitch, intensity=intensity, connected_providers=[])
    result = graph.invoke(state, config=config)

    while "__interrupt__" in result:
        interrupt_payload = result["__interrupt__"][0].value
        persona = interrupt_payload.get("persona", "Investor").upper()
        question = interrupt_payload.get("question", "")
        thinking = interrupt_payload.get("thinking", "")
        rnd = interrupt_payload.get("round", 1)

        print(f"\n" + "-" * 50)
        print(f"[{persona} — Round {rnd}]")
        if thinking:
            print(f"🧠 [Internal Analysis]:\n{thinking}\n")
        print(f"💥 [Challenge]:\n{question}\n")

        reply = input("Your answer: ").strip()
        result = graph.invoke(Command(resume=reply), config=config)

    print("\n" + "=" * 60)
    print("🏆 FINAL VERDICT & WEAKNESS BREAKDOWN")
    print("=" * 60)
    verdict = result.get("verdict", [])
    if not verdict:
        print("No specific weaknesses flagged.")
    else:
        for i, item in enumerate(verdict, 1):
            sev = item.get("severity", 3)
            print(f"{i}. [Severity {sev}/5] {item.get('issue', '')}")
            print(f"   Fix: {item.get('fix', '')}\n")

    print("Session finished successfully.")


if __name__ == "__main__":
    main()
