"""matplotlib ile çözümleri render edilmiş formül resimlerine (PNG) çeviren katman."""

from __future__ import annotations

import os


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
