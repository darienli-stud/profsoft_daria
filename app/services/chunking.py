import re


def split_text(text: str, size: int, overlap: int) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    units = _to_units(text)
    chunks: list[str] = []
    current = ""

    for unit in units:
        pieces = _split_long_unit(unit, size) if len(unit) > size else [unit]
        for piece in pieces:
            candidate = f"{current} {piece}".strip() if current else piece
            if len(candidate) <= size:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = _overlap_tail(current, overlap)
                current = f"{current} {piece}".strip() if current else piece
                if len(current) > size:
                    current = piece if len(piece) <= size else piece[:size]
            else:
                current = piece if len(piece) <= size else piece[:size]

    if current:
        chunks.append(current)
    return chunks


def _to_units(text: str) -> list[str]:
    units: list[str] = []
    paragraphs = re.split(r"\n\s*\n", text)
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        sentences = re.split(r"(?<=[.!?…])\s+", paragraph)
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                units.append(sentence)
    return units or text.split()


def _split_long_unit(unit: str, size: int) -> list[str]:
    words = unit.split()
    if not words:
        return [unit[:size]]

    parts: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            parts.append(current)
        current = word if len(word) <= size else word[:size]
    if current:
        parts.append(current)
    return parts


def _overlap_tail(text: str, overlap: int) -> str:
    if overlap <= 0 or not text:
        return ""
    tail = text[-overlap:] if len(text) > overlap else text
    if len(text) > overlap and not text[-overlap - 1].isspace():
        space = tail.find(" ")
        if space != -1:
            tail = tail[space + 1 :]
    return tail.strip()
