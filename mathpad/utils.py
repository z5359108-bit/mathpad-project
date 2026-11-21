"""Paylaşılan ayrıştırma ve normalleştirme yardımcıları."""

from __future__ import annotations

import ast
import re

import sympy as sp

_NUMBER = r"-?\d+(?:\.\d+)?"

_UNICODE_HINTS = {
    "∫": " integral ",
    "Σ": " sum ",
    "π": "pi",
    "∞": "oo",
    "×": "*",
    "·": "*",
    "⋅": "*",
    "÷": "/",
    "−": "-",
    "–": "-",
    "—": "-",
    "≤": "<=",
    "≥": ">=",
}
_SUPERSCRIPTS = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9"}

# Türkmençe özel harfleri ASCII eşdeğerlerine indirger.
_TURKMEN_FOLD = str.maketrans({
    "ä": "a", "Ä": "a", "ň": "n", "Ň": "n", "ý": "y", "Ý": "y",
    "ž": "z", "Ž": "z",
    "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ş": "s", "Ş": "S",
    "ç": "c", "Ç": "C", "ı": "i", "į": "i", "İ": "i",
    "ğ": "g", "Ğ": "G",
})


def fold_turkmen(text: str) -> str:
    """Türkmençe özgü harfleri (ä/ň/ý/ž) ASCII eşdeğerlerine indirger."""
    return text.translate(_TURKMEN_FOLD)

GENERIC_NOISE = frozenset(
    {
        "what", "is", "the", "of", "calculate", "compute", "find", "kaç", "kactir",
        "nedir", "hesapla", "bul", "sonuc", "sonuçu", "sonucu", "getir", "please",
        "bana", "bir", "value", "değer", "degeri", "değeri", "as", "from", "to", "up",
        "fonksiyon", "fonksiyonu", "fonksiyonun", "fonksiyonunun", "fonksiyonunun",
        "fonksiyonlar", "ifade", "ifadesi", "ifadesinin", "expression", "değişken",
        "elemanlı", "eleman", "kümenin", "kümesini", "sayılarının", "sayilarinin", "ise",
        "ayır", "ayir", "ayr", "ayırma", "in", "nin", "ın", "un", "ün",
        "hasapla", "hasaplan", "hasaplank", "alyn", "alynyz", "aliniz",
        "denlemesini", "denlemani", "denlemesin", "denlemelerini",
        "cak", "cakini", "ceki", "cek", "hosylayysyny", "hosylayysy", "hosylayys",
        "hosylayysyny", "hosylayysy", "hosylayys", "hosylayyşini",
        "hosylayyşy", "hosylayyş", "hosylap", "funksiyanin", "funksiya",
        "tapyar", "tapyn", "hosy",
    }
)


def _reword_functions(text: str) -> str:
    """Okul yazimlari: tg->tan, ctg->cot, lg->log10, arcsin->asin (tek yerde)."""
    text = re.sub(r"\btg\s*\(", "tan(", text)
    text = re.sub(r"\btg\s+([a-zA-Z0-9(])", r"tan \1", text)
    text = re.sub(r"\bctg\s*\(", "cot(", text)
    text = re.sub(r"\bctg\s+([a-zA-Z0-9(])", r"cot \1", text)
    text = re.sub(r"\bctg\b", "cot", text)
    text = re.sub(r"\blg\s*\(", "log10(", text)
    for plain, sympy_name in (("arcsin", "asin"), ("arccos", "acos"),
                              ("arctan", "atan"), ("arctg", "atan"),
                              ("arccot", "acot"), ("arccosec", "acsc"),
                              ("arcsec", "asec")):
        text = re.sub(rf"\b{plain}", sympy_name, text)
    return text


def _degrees_to_radians(text: str) -> str:
    """'sin(30°)' -> 'sin(30*pi/180)' (° isareti kullanildiginda)."""
    if "°" not in text and "º" not in text:
        return text
    return re.sub(r"(-?\d+(?:\.\d+)?(?:/\d+)?)\s*[°º]", r"(\1*pi/180)", text)


def normalize(text: str) -> str:
    """Unicode operatörleri ve süper üstleri sympy'nin anlayacağı biçime çevir."""
    text = fold_turkmen(text)
    text = _reword_functions(text)
    text = _degrees_to_radians(text)
    for src, dst in _UNICODE_HINTS.items():
        text = text.replace(src, dst)
    text = _decimal_comma_bracket_safe(text)
    text = re.sub(r"√\s*\(([^)]+)\)", r"sqrt(\1)", text)
    text = re.sub(r"√\s*(\w+)", r"sqrt(\1)", text)
    text = re.sub(r"√", "sqrt", text)
    for src, digit in _SUPERSCRIPTS.items():
        text = text.replace(src, f"**{digit}")
    return text


def _decimal_comma_bracket_safe(text: str) -> str:
    """'0,5x+1=3' -> '0.5x+1=3'; koseli parantez icindeki listeler (matris/varyans) korunur."""
    parts = re.split(r"(\[[^\]]*\])", text)
    return "".join(p if p.startswith("[") else replace_decimal_comma(p) for p in parts)


def _insert_implicit_multiplication(text: str) -> str:
    """'3x' -> '3*x', '2(x+1)' -> '2*(x+1)', ')(x' -> ')*(x'."""
    text = re.sub(r"(\d)\s*([a-zA-Z(])", r"\1*\2", text)
    text = re.sub(r"\)\s*([a-zA-Z(])", r")*\1", text)
    return text


_FUNC_POW_RE = re.compile(
    r"\b(sin|cos|tan|cot|sec|csc|ln|log|exp|sinh|cosh|tanh)"
    r"\^\s*(-?\d+)\s*\(([^()]*)\)",
    re.IGNORECASE,
)


def _rewrite_func_powers(text: str) -> str:
    """'sin^2(x)' -> 'sin(x)^2' (defter notasyonu)."""
    return _FUNC_POW_RE.sub(r"\1(\3)^\2", text)


def try_sympify(text: str, locals_: dict | None = None) -> sp.Basic | None:
    """Metni sympy ifadesine çevirmeyi dene; başarısızsa None döndür."""
    cleaned = normalize(text).strip().strip(",. ")
    if not cleaned or cleaned.startswith("["):
        return None
    cleaned = _rewrite_func_powers(cleaned)
    cleaned = _insert_implicit_multiplication(cleaned)
    def _log10(value, base=10):
        if base == 10:
            return sp.log(value, 10)
        return sp.log(value, base)

    local = {"sqrt": sp.sqrt, "pi": sp.pi, "oo": sp.oo, "E": sp.E, "e": sp.E, "abs": sp.Abs,
             "sin": sp.sin, "cos": sp.cos, "tan": sp.tan, "log": _log10, "log10": _log10,
             "exp": sp.exp, "ln": sp.log, "i": sp.I, "j": sp.I,
             "asin": sp.asin, "acos": sp.acos, "atan": sp.atan, "acot": sp.acot,
             "arcsin": sp.asin, "arccos": sp.acos, "arctan": sp.atan, "arctg": sp.atan,
             "arccot": sp.acot, "sec": sp.sec, "csc": sp.csc, "cot": sp.cot}
    if locals_:
        local.update(locals_)
    try:
        result = sp.sympify(cleaned, locals=local, evaluate=True, rational=True)
    except (sp.SympifyError, SyntaxError, TypeError, ValueError, AttributeError):
        return None
    if isinstance(result, (sp.Tuple, tuple, list)) or not isinstance(result, sp.Basic):
        return None
    return result


def try_sympify_lenient(text: str, locals_: dict | None = None) -> sp.Basic | None:
    """try_sympify + sondaki sözel token'ları atarak tekrar deneme ('10 denklemini çöz' -> '10')."""
    value = try_sympify(text, locals_)
    tokens = normalize(text).split()
    while value is None and tokens:
        tokens = tokens[:-1]
        candidate = " ".join(tokens)
        if not candidate.strip():
            break
        value = try_sympify(candidate, locals_)
    return value


def extract_numbers(text: str) -> list[float]:
    """Metindeki tüm sayıları sırayla çıkar (ondalık ayırıcı: nokta)."""
    return [float(m) for m in re.findall(_NUMBER, text)]


def replace_decimal_comma(text: str) -> str:
    """'0,5' biçimindeki ondalık virgülü noktaya çevir.

    Yalnızca en üst seviyede (parantez/köşeli parantez içi listeler korunur)
    'rakkam,virgül,rakkam' sıkısıklığında çevirir: '0,5x+1=3' -> '0.5x+1=3'.
    """
    out: list[str] = []
    depth = 0
    for i, ch in enumerate(text):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0 and 0 < i < len(text) - 1 and text[i - 1].isdigit() and text[i + 1].isdigit():
            out.append(".")
        else:
            out.append(ch)
    return "".join(out)


_NOISE_PREFIXES = ("hosylay", "fonksiyon", "funksiya", "denlem", "hosy", "onum", "differens", "diferens", "diferansiye", "diferansiy", "diferansiyel")


def extract_expression(text: str, extra_noise: frozenset[str] = frozenset()) -> str:
    """Soru cümlesinden matematiksel ifade adayını çıkarır.

    Yaklaşım: matematik karakterlerini koruyan bir tokenizer ile kelimelere
    böl, gürültü kelimelerini at (Türkmençe ekleri önekten tanır), + ve -
    işaretlerini koru, gerisini birleştir.
    """
    tokens = re.findall(r"[\w+\-*/^().,%]+", normalize(text))
    noise = GENERIC_NOISE | extra_noise
    kept = []
    for token in tokens:
        head = token.split("(")[0].lower()
        if head in noise or token.lower() in noise:
            continue
        if head.startswith(_NOISE_PREFIXES):
            continue
        if re.fullmatch(r"[*/^.,()]+", token):
            continue
        kept.append(token)
    return " ".join(kept).replace(",", ", ").strip()


def parse_matrix(text: str) -> sp.Matrix | None:
    """[[1,2],[3,4]] veya [[1,2;3,4]] kalıplarından matris üretir."""
    match = re.search(r"\[\s*\[[^\[\]]*\](?:\s*[,;]\s*\[[^\[\]]*\])*\s*\]", text)
    if not match:
        return None
    raw = match.group(0).replace(";", ",")
    try:
        rows = ast.literal_eval(raw)
    except (SyntaxError, ValueError, TypeError):
        return None
    try:
        return sp.Matrix(rows)
    except (ValueError, TypeError):
        return None


def strip_suffix(token: str) -> str:
    """Türkçe iyelik eklerini ('nin, in, ı, i...) tokenden atar."""
    return re.sub(r"'(n?in|nin|ın|un|ün|nuz|i|ı|s)$", "", token, flags=re.IGNORECASE)


def pick_symbol(expr: sp.Basic) -> sp.Symbol:
    """İfade içinde alfabetik olarak ilk serbest sembolü seç; yoksa x üret."""
    free = sorted(expr.free_symbols, key=lambda s: s.name)
    return free[0] if free else sp.Symbol("x")
