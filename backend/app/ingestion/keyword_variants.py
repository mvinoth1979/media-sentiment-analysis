"""
Transliterated keyword variants for Indian language relevance filtering.

Maps normalised English keyword → {lang: [script_variants]} so that
rss_collector and the orchestrator can check whether a regional-language
article mentions the brand — either in English (code-switching) or in
its local script transliteration.

Lookup is case-insensitive on the English keyword. All script variants are
used as exact Unicode substrings in keyword_matches_multilang().

To add new brands: add an entry to _VARIANTS keyed by the English keyword
(lowercase). Multiple keywords for the same brand each get their own entry.
"""

# {normalised_english_keyword: {lang_code: [script_variants, ...]}}
_VARIANTS: dict[str, dict[str, list[str]]] = {
    # ── Canara Bank ──────────────────────────────────────────────────────────
    "canara bank": {
        "ta": ["கனரா வங்கி", "கனரா பேங்க்", "Canara Bank"],
        "hi": ["केनरा बैंक", "कनारा बैंक", "Canara Bank"],
        "kn": ["ಕೆನರಾ ಬ್ಯಾಂಕ್", "Canara Bank"],
    },
    "canbank": {
        "ta": ["கேன்பேங்க்", "Canbank"],
        "hi": ["केनबैंक", "Canbank"],
        "kn": ["ಕೆನ್ಬ್ಯಾಂಕ್", "Canbank"],
    },
    # ── Reliance ─────────────────────────────────────────────────────────────
    "reliance": {
        "ta": ["ரிலையன்ஸ்", "Reliance"],
        "hi": ["रिलायंस", "Reliance"],
        "gu": ["રિલાયન્સ", "Reliance"],
        "bn": ["রিলায়েন্স", "Reliance"],
    },
    "reliance industries": {
        "ta": ["ரிலையன்ஸ் இண்டஸ்ட்ரீஸ்", "Reliance Industries"],
        "hi": ["रिलायंस इंडस्ट्रीज", "Reliance Industries"],
        "gu": ["રિલાયન્સ ઇન્ડસ્ટ્રીઝ", "Reliance Industries"],
        "bn": ["রিলায়েন্স ইন্ডাস্ট্রিজ", "Reliance Industries"],
    },
    # ── Tata ─────────────────────────────────────────────────────────────────
    "tata motors": {
        "ta": ["டாடா மோட்டார்ஸ்", "Tata Motors"],
        "hi": ["टाटा मोटर्स", "Tata Motors"],
        "kn": ["ಟಾಟಾ ಮೋಟರ್ಸ್", "Tata Motors"],
        "gu": ["ટાટા મોટર્સ", "Tata Motors"],
        "bn": ["টাটা মোটর্স", "Tata Motors"],
    },
    "tata": {
        "ta": ["டாடா", "Tata"],
        "hi": ["टाटा", "Tata"],
        "kn": ["ಟಾಟಾ", "Tata"],
        "gu": ["ટાટા", "Tata"],
        "bn": ["টাটা", "Tata"],
    },
    "tcs": {
        "ta": ["டிசிஎஸ்", "TCS"],
        "hi": ["टीसीएस", "TCS"],
        "kn": ["ಟಿಸಿಎಸ್", "TCS"],
        "gu": ["ટીસીએસ", "TCS"],
        "bn": ["টিসিএস", "TCS"],
    },
    "tanishq": {
        "ta": ["தனிஷ்க்", "Tanishq"],
        "hi": ["तनिष्क", "Tanishq"],
        "kn": ["ತನಿಷ್ಕ್", "Tanishq"],
        "gu": ["તનિષ્ક", "Tanishq"],
        "bn": ["তনিষ্ক", "Tanishq"],
    },
    "land rover": {
        "ta": ["லேண்ட் ரோவர்", "Land Rover"],
        "hi": ["लैंड रोवर", "Land Rover"],
        "kn": ["ಲ್ಯಾಂಡ್ ರೋವರ್", "Land Rover"],
        "gu": ["લેન્ડ રોવર", "Land Rover"],
        "bn": ["ল্যান্ড রোভার", "Land Rover"],
    },
    # ── Southern Railway ─────────────────────────────────────────────────────
    "southern railway": {
        "ta": ["தெற்கு ரயில்வே", "தெற்கு இந்திய இரயில்வே", "Southern Railway"],
    },
    "southern railway chennai": {
        "ta": ["தெற்கு ரயில்வே சென்னை", "Southern Railway Chennai"],
    },
    # ── CIPET ────────────────────────────────────────────────────────────────
    "cipet": {
        "ta": ["சிபெட்", "சிப்பெட்", "CIPET"],
    },
    "central institute of plastics engineering": {
        "ta": ["மத்திய பிளாஸ்டிக் பொறியியல் நிறுவனம்", "Central Institute of Plastics Engineering"],
    },
    # ── Indian Overseas Bank ─────────────────────────────────────────────────
    "indian overseas bank": {
        "ta": ["இந்தியன் ஓவர்சீஸ் வங்கி", "இண்டியன் ஓவர்சீஸ் வங்கி", "Indian Overseas Bank"],
    },
    "iob": {
        "ta": ["ஐஓபி", "IOB"],
    },
    # ── Indian Bank ──────────────────────────────────────────────────────────
    "indian bank": {
        "ta": ["இந்தியன் வங்கி", "இந்திய வங்கி", "Indian Bank"],
    },
    "indianbank": {
        "ta": ["இந்தியன் வங்கி", "IndianBank"],
    },
    # ── Bank of Baroda ───────────────────────────────────────────────────────
    "bank of baroda": {
        "ta": ["பரோடா வங்கி", "பேங்க் ஆஃப் பரோடா", "Bank of Baroda"],
        "hi": ["बैंक ऑफ बड़ौदा", "बड़ौदा बैंक", "Bank of Baroda"],
        "bn": ["ব্যাংক অব বরোদা", "Bank of Baroda"],
        "kn": ["ಬ್ಯಾಂಕ್ ಆಫ್ ಬರೋಡಾ", "Bank of Baroda"],
    },
    "bob bank": {
        "ta": ["பாப் வங்கி", "BOB"],
        "hi": ["बीओबी", "BOB"],
        "bn": ["বিওবি", "BOB"],
        "kn": ["ಬಿಒಬಿ", "BOB"],
    },
    # ── Lalitha Jewellery ────────────────────────────────────────────────────
    "lalitha jewellery": {
        "ta": ["லளிதா ஜுவல்லரி", "லளிதா நகைகள்", "Lalitha Jewellery"],
    },
    "lalitha jewels": {
        "ta": ["லளிதா நகைகள்", "Lalitha Jewels"],
    },
    # ── Pothys ───────────────────────────────────────────────────────────────
    "pothys": {
        "ta": ["பாத்தீஸ்", "பொத்தீஸ்", "Pothys"],
    },
    "pothys saree": {
        "ta": ["பாத்தீஸ் புடவை", "Pothys saree"],
    },
    # ── Ramco Cements ────────────────────────────────────────────────────────
    "ramco cements": {
        "ta": ["ராம்கோ சிமெண்ட்", "ராம்கோ சிமெண்டு", "Ramco Cements"],
    },
    "ramco cement": {
        "ta": ["ராம்கோ சிமெண்ட்", "Ramco cement"],
    },
    # ── CavinKare ────────────────────────────────────────────────────────────
    "cavinkare": {
        "ta": ["கேவின்கேர்", "CavinKare"],
    },
    "chik shampoo": {
        "ta": ["சிக் ஷாம்பு", "Chik"],
    },
    "nyle": {
        "ta": ["நைல்", "Nyle"],
    },
    "meera": {
        "ta": ["மீரா", "Meera"],
    },
    # ── Ashok Leyland ────────────────────────────────────────────────────────
    "ashok leyland": {
        "ta": ["அஷோக் லேலேண்ட்", "அசோக் லேலண்ட்", "Ashok Leyland"],
        "hi": ["अशोक लेलैंड", "अशोक लेलेंड", "Ashok Leyland"],
        "kn": ["ಅಶೋಕ್ ಲೆಲ್ಯಾಂಡ್", "Ashok Leyland"],
    },
    "ashok leyland trucks": {
        "ta": ["அஷோக் லேலேண்ட் லாரி", "Ashok Leyland trucks"],
        "hi": ["अशोक लेलैंड ट्रक", "Ashok Leyland trucks"],
        "kn": ["ಅಶೋಕ್ ಲೆಲ್ಯಾಂಡ್ ಟ್ರಕ್", "Ashok Leyland trucks"],
    },
    # ── Maruti Suzuki ────────────────────────────────────────────────────────
    "baleno": {
        "ta": ["பாலினோ", "Baleno"],
        "hi": ["बलेनो", "Baleno"],
        "kn": ["ಬಲೆನೋ", "Baleno"],
        "gu": ["બાલેનો", "Baleno"],
        "bn": ["বালেনো", "Baleno"],
    },
    "breeza": {
        "ta": ["பிரீஸா", "Brezza"],
        "hi": ["ब्रेज़ा", "Brezza"],
        "kn": ["ಬ್ರೆಜ್ಜಾ", "Brezza"],
        "gu": ["બ્રેઝા", "Brezza"],
        "bn": ["ব্রেজা", "Brezza"],
    },
    "swift": {
        "ta": ["ஸ்விஃப்ட்", "Swift"],
        "hi": ["स्विफ्ट", "Swift"],
        "kn": ["ಸ್ವಿಫ್ಟ್", "Swift"],
        "gu": ["સ્વિફ્ટ", "Swift"],
        "bn": ["সুইফট", "Swift"],
    },
    "alto k10": {
        "ta": ["ஆல்டோ", "Alto"],
        "hi": ["आल्टो", "Alto"],
        "kn": ["ಆಲ್ಟೋ", "Alto"],
        "gu": ["ઓલ્ટો", "Alto"],
        "bn": ["আল্টো", "Alto"],
    },
    "maruti": {
        "ta": ["மாருதி", "Maruti"],
        "hi": ["मारुति", "Maruti"],
        "kn": ["ಮಾರುತಿ", "Maruti"],
        "gu": ["મારુતિ", "Maruti"],
        "bn": ["মারুতি", "Maruti"],
    },
}


def get_variants_for_keywords(keywords: list[str]) -> dict[str, list[str]]:
    """Return merged {lang: [variants]} for a brand's keyword list.

    Looks up each keyword in _VARIANTS (case-insensitive) and merges all
    per-language variant lists. The result is passed to collect_portal()
    and the entity relevance gate in orchestrator.py.
    """
    merged: dict[str, list[str]] = {}
    for kw in keywords:
        entry = _VARIANTS.get(kw.lower().strip(), {})
        for lang, variants in entry.items():
            if lang not in merged:
                merged[lang] = []
            for v in variants:
                if v not in merged[lang]:
                    merged[lang].append(v)
    return merged
