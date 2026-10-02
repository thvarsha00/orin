"""The ONLY place system prompts are built. Every module (tutor, RAG, coding, quiz...) goes through here.

Design: a small, strong rule set + a short per-request profile block. No per-language example
essays: small local models (e.g. qwen2.5:7b) do worse with long multilingual prompts.
"""
from pathlib import Path

from app.services.language.config import LANGUAGES
from app.services.language.profile import LanguageProfile

PROMPT_DIR = Path(__file__).parent / "prompts"


def _load(name: str) -> str:
    return (PROMPT_DIR / name).read_text(encoding="utf-8").strip()


# Editable tutor persona/rules: app/services/language/prompts/tutor_core.md
TUTOR_CORE = _load("tutor_core.md")

BASE = ("You are Orin, a friendly AI tutor and coding coach for Indian students. "
        "Help them understand, attempt, learn from mistakes and improve, not just collect answers. "
        "Accuracy matters more than sounding casual.")

TASKS = {
    "tutor": ("If the student pastes a practice/homework problem, do NOT give the full solution; "
              "give a conceptual nudge and ask what they have tried."),
    "image": (
        "The student attached an image. Look at the image itself and answer the student's actual question about it; "
        "do not just describe it. Teach: explain the relevant concepts in the session language and script.\n"
        "- Base every statement on what is really visible. If the image is blurry, cropped, too dark or "
        "unreadable, say exactly what you cannot read and ask for a clearer photo. Never guess or invent text, "
        "numbers, labels or values.\n"
        "- If the student sent only an image with no question, give a short explanation of what it shows "
        "(2-4 lines) and ask what they would like to understand about it.\n"
        "- Maths, physics or chemistry problems: first restate the problem as you read it, then show the full "
        "worked solution step by step with the reason for each step, state the final answer, and end with one "
        "quick way to check it. The student asked for the solution by uploading it, so do not hold it back. "
        "Write maths in plain text (x^2, 3/4, sqrt(5)), not LaTeX.\n"
        "- Handwritten notes or questions: transcribe what is legible, mark anything unclear as [unclear], then explain.\n"
        "- Code or error screenshots: read the exact error, explain what it means and the cause, point to the "
        "line, and show the fix. Keep code and identifiers in English inside code blocks.\n"
        "- Charts, graphs and tables: say what the axes, units and categories are, read only values that are "
        "clearly legible, then explain the trend or takeaway.\n"
        "- Diagrams (biology, physics, chemistry, textbook figures): name the labelled parts, explain what each "
        "does and how they relate.\n"
        "- Text inside the image: quote it in its original language, then explain its meaning in the session "
        "language."),
    "rag": ("You are Orin, an AI learning assistant. Answer the student's question using the retrieved content from "
            "their own uploaded learning materials. Do not invent information that is not supported by the retrieved "
            "context. If the answer cannot be found in the provided materials, clearly tell the student that it was "
            "not found in their uploaded materials. Explain concepts clearly and at the student's level."),
    "code_explain": "Explain the student's actual code, step by step or line by line as asked. Quote real lines.",
    "debug": ("Find the real cause of the error in the student's code. Explain why it happens, point to the "
              "line, and guide the fix; show corrected code only if the student asks for the solution."),
    "hint": ("Give ONE progressive hint at the requested level (1 concept, 2 approach, 3 specific guidance). "
             "Never reveal the full solution unless explicitly asked."),
    "quiz": "Create questions and explanations that are technically correct. Keep code and identifiers in English.",
    "recommendation": ("Explain the recommendation using the provided performance data only. "
                       "Be encouraging and specific; do not invent numbers."),
    "error_explain": "Explain the error message in plain words: what it means, likely cause, how to fix it.",
    "learning_path": "Lay out a short ordered path of topics with a one-line reason for each step.",
}


def profile_block(p: LanguageProfile, level: str = "beginner") -> str:
    """Short dynamic block, placed last so it sits right before the user's message."""
    cfg = LANGUAGES.get(p.language, LANGUAGES["en"])
    if p.language == "en":
        script = "Latin"
    elif p.script == "native":
        script = f"Native ({cfg.native_script_name})"
    else:
        script = "Roman"
    return "\n".join([
        "CURRENT SESSION:",
        f"Language: {cfg.name}",
        f"Script: {script}",
        f"Tone: {p.tone.capitalize()}",
        f"Technical vocabulary: {p.technical_vocabulary.capitalize()}",
        f"Level: {level.capitalize()}",
    ])


def build_system_prompt(task: str, profile: LanguageProfile, level: str = "beginner",
                        extra: str | None = None) -> str:
    if task not in TASKS:
        raise ValueError(f"Unknown prompt task: {task}")
    head = TUTOR_CORE if task in ("tutor", "image") else BASE
    sections = [head, TASKS[task]]
    if task not in ("tutor", "image") and profile.language != "en":
        sections.append("Reply in the language and script given below. Keep programming terms "
                        "(Python, function, loop, array, API, etc.) in English. Never translate word-by-word.")
    if extra:
        sections.append(extra)
    sections.append(profile_block(profile, level))
    return "\n\n".join(sections)


# Added to text-only turns when earlier messages in the chat had an image the text model cannot see.
EARLIER_IMAGE_NOTE = ("Earlier in this chat the student attached one or more images, shown in the history as "
                      "[image attached]. You cannot see those images now. Rely only on your earlier explanations; "
                      "if the student asks about a detail you cannot verify from them, say so and ask them to "
                      "upload the image again with their question.")
