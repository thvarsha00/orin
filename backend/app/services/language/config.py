"""Central language-style configuration. To add a language, add one LanguageConfig entry here."""
from dataclasses import dataclass

# Casual address terms; seeing them lets Orin lightly mirror the student's tone.
SLANG_TOKENS = frozenset({"bro", "bhai", "yaar", "anna", "machaa", "machan", "macha", "da", "re", "dei", "bhau"})


@dataclass(frozen=True)
class LanguageConfig:
    code: str
    name: str
    native_script_name: str
    unicode_ranges: tuple[tuple[int, int], ...]
    roman_markers: frozenset[str]      # common romanized words used for detection
    roman_example: str                 # reference sample for evaluating model output; NOT sent in prompts
    codeswitch_example: str | None = None
    default_script: str = "roman"


LANGUAGES: dict[str, LanguageConfig] = {c.code: c for c in [
    LanguageConfig(
        "en", "English", "Latin", (), frozenset(),
        "Simple words: recursion is when a function calls itself.", default_script="latin"),
    LanguageConfig(
        "te", "Telugu", "Telugu script", ((0x0C00, 0x0C7F),),
        frozenset("enti ante cheppu cheppalante chey cheyyadam cheyyadaniki madhya ela ga lo unnayi naaku nenu "
                  "oka tarvata chestham kuda emiti ela".split()),
        "Simple ga cheppalante, recursion ante oka function lopala ade function ni malli call cheyyadam.",
        "Rendu kuda multiple values store cheyyadaniki use chestham. Main difference enti ante, "
        "List mutable, Tuple immutable."),
    LanguageConfig(
        "hi", "Hindi", "Devanagari", ((0x0900, 0x097F),),
        frozenset("kya hai hota hoti hote mein aur kaise nahi samjhao batao karna kaun kyun".split()),
        "Simple words mein, recursion mein ek function ke andar wahi function dobara call hota hai.",
        "Dono multiple values store karne ke liye use hote hain. Main difference ye hai ki List mutable hoti hai, "
        "but Tuple immutable hota hai."),
    LanguageConfig(
        "ta", "Tamil", "Tamil script", ((0x0B80, 0x0BFF),),
        frozenset("enna panna pannu pannuvom sollu sollanum sollanumna epdi irukku la thirumba kulla".split()),
        "Simple ah sollanumna, recursion na oru function kulla adhe function-a thirumba call panradhu.",
        "Rendum multiple values store panna use pannuvom. Main difference na, List mutable, but Tuple immutable."),
    LanguageConfig(
        "kn", "Kannada", "Kannada script", ((0x0C80, 0x0CFF),),
        frozenset("andre helu helbekandre maadu maadodu hege yaake ide alli aagi".split()),
        "Simple aagi helbekandre, recursion andre function olage ade function-na matte call maadodu."),
    LanguageConfig(
        "ml", "Malayalam", "Malayalam script", ((0x0D00, 0x0D7F),),
        frozenset("enthu aanu parayu paranjaal cheyyunnathu cheyyam aayi ennathu entha veendum".split()),
        "Simple aayi paranjaal, recursion ennathu oru function-inullil athe function-ne thanne veendum "
        "call cheyyunnathaanu."),
    LanguageConfig(
        "mr", "Marathi", "Devanagari", ((0x0900, 0x097F),),
        frozenset("mhanje sang sanga ahe kasa aani karaycha kay kaay bhashat".split()),
        "Simple bhashat sangaycha tar, recursion mhanje ek function madhun toch function punha call karne."),
    LanguageConfig(
        "bn", "Bengali", "Bengali script", ((0x0980, 0x09FF),),
        frozenset("kore bolo bolle holo ekta keno kivabe bhitore abar".split()),
        "Simple kore bolle, recursion holo ekta function-er bhitore sei function-ke abar call kora."),
]}

SUPPORTED = tuple(LANGUAGES)
