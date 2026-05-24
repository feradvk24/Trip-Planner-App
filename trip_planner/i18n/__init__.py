from . import bg
from . import en

DEFAULT_LANGUAGE = "bg"
SUPPORTED_LANGUAGES = {"bg", "en"}

ALL_TRANSLATIONS = {
    "bg": bg.TRANSLATIONS,
    "en": en.TRANSLATIONS,
}

def t(key, lang=DEFAULT_LANGUAGE):
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    return ALL_TRANSLATIONS.get(lang, {}).get(key, key)