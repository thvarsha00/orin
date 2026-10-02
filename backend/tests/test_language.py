import pytest

from app.services.language import build_system_prompt, detect, resolve_profile
from app.services.language.config import LANGUAGES
from app.services.language.prompt_builder import TASKS


@pytest.mark.parametrize("text,lang,script", [
    ("python lo loop explain chey", "te", "roman"),
    ("Python lo list and tuple madhya difference enti?", "te", "roman"),
    ("పైథాన్‌లో లూప్ అంటే ఏమిటి?", "te", "native"),
    ("python loop kya hota hai?", "hi", "roman"),
    ("पाइथन में लूप क्या होता है?", "hi", "native"),
    ("Python la list and tuple difference enna? easy ah sollu", "ta", "roman"),
])
def test_detects_language_and_script(text, lang, script):
    d = detect(text)
    assert (d.language, d.script) == (lang, script)


def test_plain_english_has_no_indian_signal():
    assert detect("What is the difference between a list and a tuple?").language is None


def test_devanagari_uses_marathi_hint():
    assert detect("पायथन म्हणजे काय", hint="mr").language == "mr"


def test_profile_defaults_and_overrides():
    p, _ = resolve_profile("te", "explain recursion")
    assert (p.language, p.script) == ("te", "roman")
    p, _ = resolve_profile("te", "python lo loop enti", script_preference="native")
    assert p.script == "native"
    p, _ = resolve_profile("te", "పైథాన్‌లో లూప్ అంటే ఏమిటి?")
    assert p.script == "native"
    p, _ = resolve_profile("en", "python loop kya hota hai, samjhao")
    assert p.language == "hi"
    assert resolve_profile("en", "hello")[0].script == "latin"


def test_slang_is_detected():
    p, _ = resolve_profile("te", "bro simple ga cheppu recursion ante enti")
    assert p.mirror_slang


def test_every_task_and_language_builds_a_prompt():
    for task in TASKS:
        for code, cfg in LANGUAGES.items():
            p, _ = resolve_profile(code, "")
            prompt = build_system_prompt(task, p, "beginner")
            assert "Orin" in prompt
            assert f"Language: {cfg.name}" in prompt
            assert "Level: Beginner" in prompt


def test_script_line_reflects_profile():
    roman, _ = resolve_profile("te", "python lo loop enti")
    native, _ = resolve_profile("te", "పైథాన్‌లో లూప్ అంటే ఏమిటి?")
    assert "Script: Roman" in build_system_prompt("tutor", roman)
    assert "Script: Native (Telugu script)" in build_system_prompt("tutor", native)
    en, _ = resolve_profile("en", "hi")
    assert "Script: Latin" in build_system_prompt("tutor", en)


def test_tutor_prompt_is_lean_and_uses_new_core():
    p, _ = resolve_profile("te", "naku tuples ardam avatledu")
    prompt = build_system_prompt("tutor", p)
    assert "TEACH, not translate" in prompt
    assert prompt.rstrip().endswith("Level: Beginner")      # profile block sits last, before the user message
    assert len(prompt) < 3500


def test_no_example_essays_and_no_persona_leak():
    p, _ = resolve_profile("te", "x")
    for task in TASKS:
        assert "lopala ade function" not in build_system_prompt(task, p)   # old recursion anchor
    assert "TEACH, not translate" not in build_system_prompt("debug", p)
