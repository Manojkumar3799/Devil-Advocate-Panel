import sys
import streamlit
import langchain
import reportlab
import supabase
import vecs

print("Python version:", sys.version)
print("Streamlit:", streamlit.__version__)
print("LangChain:", langchain.__version__)
print("ReportLab:", reportlab.__version__)
print("Supabase:", supabase.__version__)
print("Vecs:", vecs.__version__)

from core.state import initial_state
print("core.state loaded OK")

from core.prompts import build_persona_system_prompt
print("core.prompts loaded OK")

from core.reasoning import extract_reasoning
print("core.reasoning loaded OK")

from core.tools import get_tools_for_persona
print("core.tools loaded OK")

from core.llm import PanelLLM
print("core.llm loaded OK")

from export.pdf import generate_panel_pdf
print("export.pdf loaded OK")

# Test PDF generation
test_pdf = generate_panel_pdf(
    pitch_text="Test pitch for DevPulse AI",
    intensity="normal",
    transcript=[{
        "persona": "vc",
        "round": 1,
        "thinking": "Validating moat and founder pedigree.",
        "question": "Where is your proprietary moat?",
        "user_reply": "We have patented algorithms and 14 enterprise design partners.",
    }],
    verdict=[{
        "issue": "Moat relies on software that can be copied by incumbents.",
        "severity": 4,
        "fix": "Focus on high-switching-cost data integration.",
    }],
)
print(f"Test PDF generated successfully! Size: {len(test_pdf)} bytes")

from db.client import get_supabase_client
print("db.client loaded OK")

print("EVERYTHING VERIFIED AND WORKING SMOOTHLY!")
