import type { Language } from "../types";

export const LANGUAGES: { code: Language; label: string; native: string }[] = [
  { code: "en", label: "English", native: "English" },
  { code: "te", label: "Telugu", native: "తెలుగు" },
  { code: "hi", label: "Hindi", native: "हिन्दी" },
  { code: "ta", label: "Tamil", native: "தமிழ்" },
  { code: "kn", label: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ml", label: "Malayalam", native: "മലയാളം" },
  { code: "mr", label: "Marathi", native: "मराठी" },
  { code: "bn", label: "Bengali", native: "বাংলা" },
];

// Example question shown on the empty Tutor screen, in the selected language.
// UI text only (not sent to the AI). "roman" is used unless the user picked native script.
const EXAMPLES: Record<Language, { roman: string; native: string }> = {
  en: { roman: "What's the difference between a list and a tuple in Python?", native: "What's the difference between a list and a tuple in Python?" },
  te: { roman: "Python lo list and tuple difference enti?", native: "Python లో list మరియు tuple మధ్య తేడా ఏమిటి?" },
  hi: { roman: "Python mein list aur tuple mein kya difference hai?", native: "Python में list और tuple में क्या अंतर है?" },
  ta: { roman: "Python la list ku tuple ku enna difference?", native: "Python-ல் list-க்கும் tuple-க்கும் என்ன வித்தியாசம்?" },
  kn: { roman: "Python alli list mattu tuple nadhuvina vyatyasa enu?", native: "Python ನಲ್ಲಿ list ಮತ್ತು tuple ನಡುವಿನ ವ್ಯತ್ಯಾಸ ಏನು?" },
  ml: { roman: "Python il list um tuple um thammil ulla vyathyasam enthaanu?", native: "Python-ൽ list-ഉം tuple-ഉം തമ്മിലുള്ള വ്യത്യാസം എന്താണ്?" },
  mr: { roman: "Python madhye list ani tuple madhye kaay farak aahe?", native: "Python मध्ये list आणि tuple मध्ये काय फरक आहे?" },
  bn: { roman: "Python e list ar tuple er moddhe parthokyo ki?", native: "Python-এ list আর tuple-এর মধ্যে পার্থক্য কী?" },
};

export const exampleQuestion = (lang: Language, script: "auto" | "roman" | "native") =>
  EXAMPLES[lang][script === "native" ? "native" : "roman"];
