"""LaTeX -> Unicode düz metin dönüştürücü (defter modu yazıcısı için).

Yalnızca bu projenin çözücülerinin ürettiği komut kümesini kapsar:
frac, sqrt, ln/log, lim, int, pm/leq/geq/neq/cdot/delta/pi/to/infty/text,
super/subscript gibi. Çıktıda ham '\\komut' kalmamalıdır.
"""

from __future__ import annotations

import re

_SYMBOLS = {
    r"\nexists": "∄",
    r"\exists": "∃",
    r"\Rightarrow": "⇒",
    r"\Leftrightarrow": "⇔",
    r"\neq": "≠",
    r"\ne": "≠",
    r"\leq": "≤",
    r"\geq": "≥",
    r"\pm": "±",
    r"\mp": "∓",
    r"\cdots": "…",
    r"\cdot": "·",
    r"\times": "×",
    r"\div": "÷",
    r"\pi": "π",
    r"\Delta": "Δ",
    r"\delta": "δ",
    r"\theta": "θ",
    r"\alpha": "α",
    r"\beta": "β",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\infty": "∞",
    r"\varnothing": "∅",
    r"\emptyset": "∅",
    r"\cup": "∪",
    r"\cap": "∩",
    r"\notin": "∉",
    r"\subset": "⊂",
    r"\forall": "∀",
    r"\exists": "∃",
    r"\to": "→",
    r"\rightarrow": "→",
    r"\mapsto": "↦",
    r"\approx": "≈",
    r"\arcsin": "arcsin",
    r"\arccos": "arccos",
    r"\arctan": "arctan",
    r"\sin": "sin",
    r"\cos": "cos",
    r"\tan": "tan",
    r"\cot": "cot",
    r"\sec": "sec",
    r"\csc": "csc",
    r"\exp": "exp",
    r"\max": "maks",
    r"\min": "min",
    r"\ln": "ln",
    r"\log": "log",
    r"\lim": "lim",
    r"\le": "≤",
    r"\ge": "≥",
    r"\colon": ":",
    r"\mid": "|",
    r"\|": "‖",
    r"\int": "∫",
    r"\sum": "Σ",
    r"\prod": "Π",
    r"\mathbb{Z}": "ℤ",
    r"\mathbb{R}": "ℝ",
    r"\mathbb{N}": "ℕ",
    r"\mathbb{Q}": "ℚ",
    r"\mathbb{C}": "ℂ",
    r"\mathrm{i}": "i",
    r"\mathrm{I}": "i",
    r"\in ": "∈",
    r"\!": "",
    r"\,": " ",
    r"\;": " ",
    r"\:": " ",
    r"\ ": " ",
    r"\\": " ",
    r"\%": "%",
    r"\{": "{",
    r"\}": "}",
}

_SUPER = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "−": "⁻", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "x": "ˣ", "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
    "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "j": "ʲ", "k": "ᵏ", "l": "ˡ", "m": "ᵐ",
    "o": "ᵒ", "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ", "v": "ᵛ",
    "w": "ʷ", "y": "ʸ", "z": "ᶻ",
}

_SUB = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "−": "₋", "(": "₍", ")": "₎",
    "n": "ₙ", "i": "ᵢ", "x": "ₓ", "k": "ₖ",
}

_TEXT_PREFIXES = (r"\text", r"\mathrm", r"\operatorname", r"\mathit")
_BIG_PREFIXES = (r"\Bigl", r"\Bigr", r"\bigl", r"\bigr", r"\Big", r"\big")
_FRAC_PREFIXES = (r"\dfrac", r"\tfrac", r"\frac")


def _brace_block(text: str, start: int) -> tuple[str, int]:
    """start, '{' karakterini gösterir; içeriği ve kapanış sonrası indeksi döndürür."""
    depth = 0
    for i in range(start, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
    return text[start + 1:], len(text)


def _simple_atom(expr: str) -> bool:
    expr = expr.strip()
    if not expr:
        return False
    if any(op in expr for op in "+-*−·/×≤≥<>=±"):
        return False
    return True


def _inner(text: str) -> str:
    return _convert(text) if "\\" in text else text


def _convert_frac(text: str) -> str:
    for prefix in _FRAC_PREFIXES:
        while True:
            idx = text.find(prefix + "{")
            if idx < 0:
                break
            num, after_num = _brace_block(text, idx + len(prefix))
            if after_num >= len(text) or text[after_num] != "{":
                text = text[:idx] + num + text[after_num:]
                continue
            den, after_den = _brace_block(text, after_num)
            if not _simple_atom(num):
                num = f"({num})"
            if not _simple_atom(den):
                den = f"({den})"
            text = text[:idx] + f"{num}/{den}" + text[after_den:]
    return text


def _convert_sqrt(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        if text.startswith(r"\sqrt", i):
            j = i + 5
            if j < n and text[j] == "[":
                end = text.find("]", j)
                if end > j:
                    body, j_next = _brace_block(text, end + 1) if end + 1 < n and text[end + 1] == "{" \
                        else (text[end + 1:], n)
                    out.append(f"{_convert_sqrt(text[j + 1:end])}√({body})")
                    i = j_next
                    continue
            if j < n and text[j] == "{":
                body, j_next = _brace_block(text, j)
                body_out = _inner(body)
                out.append(f"√({body_out})" if not _simple_atom(body_out) else "√" + body_out)
                i = j_next
                continue
            out.append("√")
            i = j
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _convert_scripts(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "^":
            j = i + 1
            if j < n and text[j] == "{":
                inner, after = _brace_block(text, j)
            else:
                j2 = j
                if j2 < n and text[j2] in "-−":
                    j2 += 1
                while j2 < n and (text[j2].isalnum() or text[j2] in "()"):
                    j2 += 1
                inner, after = text[j:j2], j2
            inner = inner.strip()
            if inner == "1":
                out.append("")
                i = after
                continue
            if any(op in inner for op in "+−*·/×≤≥<>") or "−" in inner:
                out.append(f"^({inner.replace(' ', '')})")
                i = after
                continue
            if " " in inner:
                inner = inner.replace(" ", "")
            missing = [c for c in inner if c not in _SUPER]
            if missing:
                out.append(f"^({inner})")
            else:
                out.append("".join(_SUPER[c] for c in inner))
            i = after
            continue
        if ch == "_" and (i == 0 or text[i - 1] != "\\"):
            j = i + 1
            if j < n and text[j] == "{":
                inner, after = _brace_block(text, j)
            else:
                inner = text[j] if j < n else ""
                after = j + 1
            inner = inner.strip()
            if inner and all(c in _SUB for c in inner):
                out.append("".join(_SUB[c] for c in inner))
            elif inner:
                out.append(f"_({inner})")
            i = after
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def _convert_text_cmds(text: str) -> str:
    out = []
    i = 0
    n = len(text)
    while i < n:
        if any(text.startswith(p, i) for p in _TEXT_PREFIXES):
            brace = text.find("{", i)
            if brace >= 0 and brace - i <= len(r"\operatorname"):
                body, after = _brace_block(text, brace)
                out.append(body)
                i = after
                continue
        if any(text.startswith(p, i) for p in _BIG_PREFIXES):
            k = i + len(next(p for p in _BIG_PREFIXES if text.startswith(p, i)))
            while k < n and text[k] not in "([{)]}.|":
                k += 1
            out.append(text[k] if k < n else "")
            i = k + 1
            continue
        if text.startswith((r"\ldots", r"\dots"), i):
            out.append("…")
            i += 6
            continue
        if text.startswith((r"\dfrac{", r"\tfrac{"), i):
            out.append(r"\frac")
            i += 6
            continue
        if text.startswith((r"\left", r"\right"), i):
            prefix_len = 5 if text.startswith(r"\left", i) else 6
            k = i + prefix_len
            while k < n and text[k] not in "([{)]}.|":
                k += 1
            out.append(text[k] if k < n else "")
            i = k + 1
            continue
        if text.startswith((r"\begin{", r"\end{"), i):
            body, after = _brace_block(text, text.find("{", i))
            if body in ("pmatrix", "bmatrix", "matrix", "cases"):
                out.append("")
            i = after
            if text.startswith("&", i):
                i += 1
                out.append("  ")
            continue
        if text.startswith(r"\item", i):
            out.append("•")
            i += 5
            continue
        if text[i] == "$":
            i += 1
            continue
        out.append(text[i])
        i += 1
    return "".join(out)


def _longest_first(pairs):
    return sorted(pairs, key=lambda kv: -len(kv[0]))


_SYMBOL_PAIRS = _longest_first(list(_SYMBOLS.items()))


def _convert(text: str) -> str:
    text = _convert_text_cmds(text)
    for src, dst in _SYMBOL_PAIRS:
        text = text.replace(src, dst)
    text = _convert_frac(text)
    text = _convert_sqrt(text)
    text = _convert_scripts(text)
    text = re.sub(r"\\[A-Za-z]+", " ", text)
    text = re.sub(r"\{\(\s*([^{}]*?)\s*\)\}", r"(\1)", text)
    text = re.sub(r"\{([^{}:]{1,24})\}", r"\1", text)
    text = text.replace("  ", " ").strip()
    return text


def latex_to_unicode(text: str) -> str:
    """Ham LaTeX satırını deftere yazılacak unicode metne çevirir."""
    try:
        return _convert(text)
    except Exception:  # noqa: BLE001
        return re.sub(r"\\[A-Za-z]+\s*", " ", text)
