"""matplotlib ile çözümleri render edilmiş formül resimlerine (PNG) çeviren katman."""

from __future__ import annotations

import os
import re

from matplotlib import mathtext

_PARSER = mathtext.MathTextParser("agg")

_SUPER_MAP = {
    "\u2070": "0", "\u00b9": "1", "\u00b2": "2", "\u00b3": "3",
    "\u2074": "4", "\u2075": "5", "\u2076": "6", "\u2077": "7",
    "\u2078": "8", "\u2079": "9", "\u207b": "-", "\u207a": "+",
    "\u1d49": "e", "\u02e3": "x", "\u207f": "n", "\u1d4f": "k",
    "\u2071": "i", "\u1d43": "a",
}
_SUPER_RUN = re.compile("[" + re.escape("".join(_SUPER_MAP)) + "]+")
_SUB_MAP = {
    "\u2080": "0", "\u2081": "1", "\u2082": "2", "\u2083": "3",
    "\u2084": "4", "\u2085": "5", "\u2086": "6", "\u2087": "7",
    "\u2088": "8", "\u2089": "9", "\u208b": "-", "\u208a": "+",
}
_SUB_RUN = re.compile("[" + re.escape("".join(_SUB_MAP)) + "]+")

_SYMBOLS = (
    ("\u2212", "-"),
    ("\u00b7", r"\cdot "),
    ("\u03c0", r"\pi"),
    ("\u0394", r"\Delta"),
    ("\u00b1", r"\pm "),
    ("\u2264", r"\leq "),
    ("\u2265", r"\geq "),
    ("\u2260", r"\neq "),
    ("\u21d2", r"\Rightarrow "),
    ("\u21d4", r"\Leftrightarrow "),
    ("\u2208", r"\in "),
    ("\u222a", r"\cup "),
    ("\u2229", r"\cap "),
    ("\u2124", r"\mathbb{Z}"),
    ("\u211d", r"\mathbb{R}"),
    ("\u211a", r"\mathbb{Q}"),
    ("\u2115", r"\mathbb{N}"),
    ("\u221e", r"\infty"),
    ("\u2205", r"\varnothing"),
    ("\u2192", r"\to "),
    ("\u222b", r"\int"),
    ("\u2032", "'"),
    ("\u2033", "''"),
)

_FUNCS = (
    "arcsin", "arccos", "arctan", "arccot",
    "sin", "cos", "tan", "cot", "sec", "csc",
    "lim", "ln", "log", "exp",
)

_RUN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789^_{}\\.+\u03c0\u0394")


def _maps(text: str) -> str:
    for token, replacement in _SYMBOLS:
        text = text.replace(token, replacement)
    for cmd in _FUNCS:
        text = re.sub(rf"(?<![A-Za-z\\]){cmd}(?![A-Za-z])", rf"\\{cmd} ", text)
    return text


def _replace_runs(text: str) -> str:
    text = _SUPER_RUN.sub(
        lambda m: "^{" + "".join(_SUPER_MAP[c] for c in m.group(0)) + "}", text)
    text = _SUB_RUN.sub(
        lambda m: "_{" + "".join(_SUB_MAP[c] for c in m.group(0)) + "}", text)
    return text


def _pow_paren_pass(text: str) -> str:
    text = re.sub(r"\^\(([^()]*)\)", r"^{\1}", text)
    return re.sub(r"_\(([^()]*)\)", r"_{\1}", text)


def _balanced(text: str, open_i: int) -> tuple[int, int] | None:
    depth = 0
    for i in range(open_i, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                return open_i, i + 1
    return None


def _balanced_back(text: str, close_i: int) -> tuple[int, int] | None:
    depth = 0
    for i in range(close_i, -1, -1):
        if text[i] == ")":
            depth += 1
        elif text[i] == "(":
            depth -= 1
            if depth == 0:
                return i, close_i + 1
    return None


def _brace_group_start(text: str, close_i: int) -> tuple[int, int] | None:
    """close_i '}' ise eşleşen '{' konumunu döner; değilse None."""
    if close_i < 0 or text[close_i] != "}":
        return None
    depth = 0
    for i in range(close_i, -1, -1):
        if text[i] == "}":
            depth += 1
        elif text[i] == "{":
            depth -= 1
            if depth == 0:
                return i, close_i + 1
    return None


def _back_token(text: str, end: int) -> int:
    """end'e bitişik (boşluksuz) terim grubunun başlangıcını verir; yoksa end."""
    if end == 0:
        return 0
    if text[end - 1] == "}":
        span = _brace_group_start(text, end - 1)
        if not span:
            return end
        if span[0] > 0 and text[span[0] - 1] in ("^", "_"):
            return _back_token(text, span[0] - 1)
        return end
    if text[end - 1] == ")":
        span = _balanced_back(text, end - 1)
        if span:
            start = span[0]
            while start > 0 and text[start - 1] == ")":
                span2 = _balanced_back(text, start - 1)
                if not span2:
                    break
                start = span2[0]
            if start > 0 and text[start - 1] in _RUN_CHARS:
                j = start - 1
                while j >= 0 and text[j] in _RUN_CHARS:
                    j -= 1
                start = j + 1
            return start
    j = end
    if text[j - 1] in _RUN_CHARS:
        while j > 0 and text[j - 1] in _RUN_CHARS:
            j -= 1
        return j
    if text[j - 1] == " ":
        k = j - 1
        while k > 0 and text[k - 1] == " ":
            k -= 1
        if k > 0 and text[k - 1] == ")":
            span = _balanced_back(text, k - 1)
            if span:
                start = span[0]
                while start > 0 and text[start - 1] == ")":
                    span2 = _balanced_back(text, start - 1)
                    if not span2:
                        break
                    start = span2[0]
                return start
    return end


def _frac_pass(text: str) -> str:
    chars = list(text)
    depth = 0
    i = 0
    while i < len(chars):
        if chars[i] == "{":
            depth += 1
        elif chars[i] == "}":
            depth -= 1
        elif chars[i] == "/" and depth == 0:
            end = i + 1
            den = None
            if end < len(chars) and chars[end] == "(":
                span = _balanced(text, end)
                if span:
                    end = span[1]
                    while end + 1 < len(chars) and chars[end] == "^" and chars[end + 1] == "{":
                        depth2 = 0
                        matched = None
                        for k2 in range(end + 1, len(chars)):
                            if chars[k2] == "{":
                                depth2 += 1
                            elif chars[k2] == "}":
                                depth2 -= 1
                                if depth2 == 0:
                                    matched = k2 + 1
                                    break
                        if matched is None:
                            break
                        end = matched
                    tail = "".join(chars[span[1]:end])
                    if tail:
                        den = text[span[0]: span[1]] + tail
                    else:
                        den = text[span[0] + 1: span[1] - 1]
            if den is None:
                k = end
                while k < len(chars) and chars[k] in _RUN_CHARS:
                    k += 1
                den = "".join(chars[i + 1:k])
                end = k
                if k < len(chars) and chars[k] == " " and k + 1 < len(chars) and chars[k + 1] == "(" \
                        and den and den[-1].isalpha() and not den[-1] == "\\":
                    fspan = _balanced(text, k + 1)
                    if fspan:
                        den = den + " (" + text[fspan[0] + 1: fspan[1] - 1] + ")"
                        end = fspan[1]
            if not den:
                i += 1
                continue
            start = _back_token(text, i)
            if start == i:
                i += 1
                continue
            num = "".join(chars[start:i]).strip()
            replacement = "\\frac{" + num + "}{" + den + "}"
            new_text = "".join(chars[:start]) + replacement + "".join(chars[end:])
            return _frac_pass(new_text)
        i += 1
    return "".join(chars)


def _sqrt_pass(text: str) -> str:
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in ("\u221a", "\u221b"):
            j = i + 1
            group = None
            if j < len(text) and text[j] == "(":
                span = _balanced(text, j)
                if span:
                    group = text[span[0] + 1: span[1] - 1]
                    j = span[1]
            if group is None:
                k = j
                while k < len(text) and text[k] in _RUN_CHARS:
                    k += 1
                group = text[j:k]
                j = k
            cmd = "\\sqrt[3]" if ch == "\u221b" else "\\sqrt"
            out.append(cmd + "{" + group.strip() + "}")
            i = j
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def chain_to_mathtext(line: str) -> str | None:
    """Defter zincir satırını matplotlib mathtext'e çevirir.

    Dönüşümde matematiksel içerik değişmez; ayrıştırılamayan satır için None
    döner ve çağıran düz Unicode metni kullanır (ham LaTeX asla çıkmaz).
    """
    text = line.strip()
    text = text.replace("{", "\\{").replace("}", "\\}")
    text = _maps(text)
    text = _replace_runs(text)
    text = _pow_paren_pass(text)
    text = _sqrt_pass(text)
    text = _frac_pass(text)
    text = re.sub(r"\s+", " ", text)
    try:
        _PARSER.parse(f"${text}$", dpi=100)
    except Exception:  # noqa: BLE001
        return None
    return text


def _prep_math(tex: str | None) -> str | None:
    if not tex:
        return None
    out = tex.strip()
    if out.startswith("$") and out.endswith("$") and len(out) > 1:
        out = out[1:-1]
    return out if out else None


def _render_math(fig, tex: str, x: float, y: float, size: float = 15.0) -> None:
    from matplotlib import mathtext

    parser = mathtext.MathTextParser("agg")
    try:
        parser.parse(f"${tex}$", dpi=100)
    except Exception:
        fig.text(x, y, tex, fontsize=size - 2, va="top", family="DejaVu Sans")
        return
    fig.text(x, y, f"${tex}$", fontsize=size, va="top")


def solution_to_png(solution, path: str, dpi: int = 160) -> str:
    """Bir Solution'ı formülleri render edilmiş tek bir PNG dosyasına yaz."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"

    rows: list[tuple[str, str]] = [("title", f"Soru: {solution.question}")]
    for n, step in enumerate(solution.steps, 1):
        rows.append(("label", f"{n}. {step.title}"))
        tex = _prep_math(step_to_png_latex(step))
        if tex:
            rows.append(("math", tex))
        if step.detail:
            rows.append(("detail", f"({step.detail})"))
    result_tex = _prep_math(solution.result_tex)
    if result_tex:
        rows.append(("result_math", result_tex))
    else:
        rows.append(("result_text", solution.result_text))

    fig = plt.figure(figsize=(9.0, max(2.0, 0.55 * len(rows) + 0.6)))
    fig.patch.set_facecolor("white")

    y = 0.97
    for kind, text in rows:
        if kind == "title":
            fig.text(0.06, y, text, fontsize=12, fontweight="bold", va="top")
            y -= 0.085
        elif kind == "label":
            fig.text(0.09, y, text, fontsize=11.5, va="top", color="#20406a")
            y -= 0.075
        elif kind == "math":
            _render_math(fig, text, 0.13, y)
            y -= 0.085
        elif kind == "detail":
            fig.text(0.13, y, text, fontsize=9.5, va="top", color="gray")
            y -= 0.06
        elif kind == "result_math":
            fig.text(0.06, y, "SONUÇ:", fontsize=12.5, fontweight="bold", va="top")
            _render_math(fig, text, 0.24, y + 0.006, size=16)
            y -= 0.1
        else:
            fig.text(0.06, y, f"SONUÇ: {text}", fontsize=12.5, fontweight="bold", va="top")
            y -= 0.1

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.25, facecolor="white")
    plt.close(fig)
    return path


def step_to_png_latex(step) -> str | None:
    from .latex import step_to_latex

    body = step_to_latex(step)
    return body or None


def save_solution_png(solution, folder: str, index: int, prefix: str = "soru") -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{prefix}_{index:03d}.png")
    return solution_to_png(solution, path)


def defter_to_png(solution, path: str, dpi: int = 160) -> str:
    """Defter zincirini render edilmiş formüllerle tek bir PNG dosyasına yazar.

    Her zincir satırı mathtext'e çevrilip gerçek formül olarak çizilir;
    çevrilemeyen satır düz Unicode metin olarak kalır.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from .defter import defter_satirlar

    plt.rcParams["font.family"] = "DejaVu Sans"

    rows: list[tuple[str, str]] = [("title", f"Soru: {solution.question}")]
    for line in defter_satirlar(solution):
        rows.append(("math", line))

    fig = plt.figure(figsize=(9.0, max(2.0, 0.6 * len(rows) + 0.6)))
    fig.patch.set_facecolor("white")

    y = 0.95
    for kind, text in rows:
        if kind == "title":
            fig.text(0.06, y, text, fontsize=12, fontweight="bold", va="top", wrap=True)
            y -= 0.1
        else:
            tex = chain_to_mathtext(text)
            if tex:
                _render_math(fig, tex, 0.09, y)
            else:
                fig.text(0.09, y, text, fontsize=13, va="top", family="DejaVu Sans")
            y -= 0.09

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    fig.savefig(path, dpi=dpi, bbox_inches="tight", pad_inches=0.25, facecolor="white")
    plt.close(fig)
    return path
