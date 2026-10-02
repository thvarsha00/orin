from dataclasses import asdict, dataclass


@dataclass
class LanguageProfile:
    language: str = "en"
    script: str = "latin"                 # latin | roman | native
    tone: str = "conversational"
    technical_vocabulary: str = "english"
    formality: str = "casual"
    mirror_slang: bool = False

    def to_dict(self) -> dict:
        return asdict(self)
