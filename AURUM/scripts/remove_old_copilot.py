from pathlib import Path

src = Path("dashboard/aurum_mission_control.py").read_text(encoding="utf-8")

# Find and remove the old ask_copilot function
start_marker = "def ask_copilot(question: str, state: dict[str, Any], rec: dict[str, Any], events: list[dict[str, Any]]) -> dict[str, Any]:"
end_marker = "    write_json(COPILOT_RESPONSE_PATH, response)\n    return response"

start_idx = src.find(start_marker)
end_idx = src.find(end_marker, start_idx) + len(end_marker)

if start_idx == -1:
    print("Old function not found — already removed or different format.")
else:
    src = src[:start_idx] + "# Old rule-based copilot removed — Groq LLM used via copilot_service.py\n" + src[end_idx:]
    Path("dashboard/aurum_mission_control.py").write_text(src, encoding="utf-8")
    print("Removed old ask_copilot function.")

# Verify
src2 = Path("dashboard/aurum_mission_control.py").read_text(encoding="utf-8")
print("Has old function:", "def ask_copilot" in src2)
print("Has Groq import:", "answer_question" in src2)

import py_compile
py_compile.compile("dashboard/aurum_mission_control.py", doraise=True)
print("Syntax OK.")