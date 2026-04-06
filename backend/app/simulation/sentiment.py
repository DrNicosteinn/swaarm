"""Simple keyword-based sentiment analysis for simulation content.

Lightweight heuristic — no external dependencies, no LLM calls.
Used to assign sentiment scores to posts and comments during simulation.
"""

# Negative indicators (German social media)
NEGATIVE_WORDS = {
    "skandal", "schockiert", "empört", "unfair", "unverantwortlich",
    "katastrophe", "schlimm", "schrecklich", "wütend", "enttäuscht",
    "protest", "streik", "kündigung", "entlassung", "stellenabbau",
    "verlust", "krise", "angst", "sorge", "besorgt", "verzweifelt",
    "ungerecht", "schlag", "frechheit", "unverschämt", "unerhört",
    "traurig", "betroffen", "erschüttert", "fassungslos", "inakzeptabel",
    "versagen", "fehler", "problem", "kritik", "warnung", "risiko",
    "negativ", "schlecht", "mangelhaft", "gefährlich", "bedenklich",
}

# Positive indicators
POSITIVE_WORDS = {
    "gut", "positiv", "innovation", "chance", "zukunft", "fortschritt",
    "unterstützung", "solidarität", "verbesserung", "erfolgreich",
    "gewinn", "wachstum", "hoffnung", "optimistisch", "mutig",
    "richtig", "wichtig", "notwendig", "klug", "strategisch",
    "nachhaltig", "verantwortungsvoll", "professionell", "fair",
    "konstruktiv", "lösung", "engagement", "zusammenarbeit",
    "danke", "bravo", "toll", "super", "großartig", "hervorragend",
    "effizient", "modern", "digital", "transformation",
}

# Intensifiers
INTENSIFIERS = {"sehr", "extrem", "absolut", "total", "völlig", "unglaublich", "massiv"}


def compute_text_sentiment(text: str) -> float:
    """Compute sentiment score from text content.

    Returns float between -1.0 (very negative) and 1.0 (very positive).
    0.0 = neutral.
    """
    if not text:
        return 0.0

    words = text.lower().split()
    words_set = set()
    for w in words:
        cleaned = w.strip(".,!?;:()\"'#@")
        if cleaned:
            words_set.add(cleaned)

    neg_count = len(words_set & NEGATIVE_WORDS)
    pos_count = len(words_set & POSITIVE_WORDS)
    intensifier_count = len(words_set & INTENSIFIERS)

    if neg_count == 0 and pos_count == 0:
        return 0.0

    # Intensifiers amplify the dominant sentiment
    amplifier = 1.0 + intensifier_count * 0.3

    total = neg_count + pos_count
    if total == 0:
        return 0.0

    # Score between -1 and 1
    raw_score = (pos_count - neg_count) / total
    score = raw_score * amplifier

    return max(-1.0, min(1.0, score))
