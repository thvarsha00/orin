import re
from dataclasses import dataclass

from app.services.language.config import LANGUAGES, SLANG_TOKENS
from app.services.language.profile import LanguageProfile


@dataclass
class Detection:
    language: str | None = None    # None = no Indian-language signal (e.g. plain English)
    script: str | None = None      # native | roman | None
    confident: bool = False
    slang: bool = False


def _native_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ch in text:
        cp = ord(ch)
        for code, cfg in LANGUAGES.items():
            if any(lo <= cp <= hi for lo, hi in cfg.unicode_ranges):
                counts[code] = counts.get(code, 0) + 1
    return counts


def detect(text: str, hint: str = "en") -> Detection:
    """Heuristic detector: native-script by Unicode block, romanized by marker words.
    `hint` disambiguates Devanagari between Hindi and Marathi."""
    tokens = re.findall(r"[a-z']+", text.lower())
    slang = any(t in SLANG_TOKENS for t in tokens)
    letters = sum(1 for c in text if c.isalpha())

    counts = _native_counts(text)
    native_total = sum(counts.values())
    if native_total >= 2 and letters and native_total / letters >= 0.2:
        # Devanagari is shared by Hindi and Marathi, so both get counted: prefer the hint.
        if "hi" in counts and "mr" in counts:
            lang = "mr" if hint == "mr" else "hi"
        else:
            lang = max(counts, key=counts.get)
        return Detection(lang, "native", True, slang)

    scores = {code: sum(t in cfg.roman_markers for t in tokens)
              for code, cfg in LANGUAGES.items() if cfg.roman_markers}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    if ranked and ranked[0][1] >= 1 and (len(ranked) == 1 or ranked[0][1] > ranked[1][1]):
        return Detection(ranked[0][0], "roman", ranked[0][1] >= 2, slang)
    return Detection(None, None, False, slang)


def resolve_profile(selected_language: str, message: str, script_preference: str = "auto",
                    last_script: str | None = None) -> tuple[LanguageProfile, Detection]:
    """Combine the UI language, the student's saved preference and what they just typed."""
    hint = selected_language if selected_language in ("hi", "mr") else "hi"
    det = detect(message, hint)
    language = det.language if (det.confident and det.language) else selected_language
    if language not in LANGUAGES:
        language = "en"

    if language == "en":
        script = "latin"
    elif script_preference in ("roman", "native"):
        script = script_preference                       # explicit choice always wins
    elif det.script and det.language == language:
        script = det.script                              # mirror what they typed
    else:
        script = last_script or LANGUAGES[language].default_script

    return LanguageProfile(language=language, script=script, mirror_slang=det.slang), det
