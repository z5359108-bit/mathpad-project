"""Defter: çözümleri LaTeX bibilgileriyle Markdown ve HTML'e yazan kayıt tutucu."""

from __future__ import annotations

import datetime
from pathlib import Path

from .rendering.latex import step_to_latex
from .rendering.text import step_to_text
from .solvers.base import Solution


class Notebook:
    """Çözümleri toplar; Markdown (MathJax uyumlu $$ blokları) ve HTML üretir."""

    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>__TITLE__</title>
<script>
MathJax = { tex: { inlineMath: [['$', '$']], displayMath: [['$$', '$$']] } };
</script>
<script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
<style>
  body { font-family: -apple-system, 'Segoe UI', sans-serif; max-width: 800px;
         margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
  .question { background: #eef3ff; border-left: 4px solid #3b5bdb;
              padding: 0.5rem 1rem; border-radius: 4px; }
  .result { background: #eafaf1; border-left: 4px solid #2f9e44;
            padding: 0.5rem 1rem; border-radius: 4px; }
  ol.steps > li { margin-bottom: 0.6rem; }
  footer { color: #777; font-size: 0.85rem; margin-top: 3rem; }
</style>
</head>
<body>
<h1>__TITLE__</h1>
__BODY__
<footer>__FOOTER__</footer>
</body>
</html>
"""

    def __init__(self, title: str = "Matematik Defteri"):
        self.title = title
        self.solutions: list[Solution] = []

    def add(self, solution: Solution) -> Solution:
        self.solutions.append(solution)
        return solution

    def markdown(self) -> str:
        parts = [f"# {self.title}", ""]
        for i, sol in enumerate(self.solutions, 1):
            parts.append(f"## {i}. {sol.title}")
            parts.append("")
            parts.append(f"> **Soru:** {sol.question}  ")
            parts.append(f"> *(çözücü: `{sol.solver}`)*")
            parts.append("")
            parts.append(f"**Sonuç:** $${sol.result_tex}$$")
            parts.append("")
            if sol.steps:
                parts.append("**Çözüm adımları:**")
                parts.append("")
                for n, step in enumerate(sol.steps, 1):
                    parts.append(f"{n}. **{step.title}**")
                    if step.detail:
                        parts.append(f"   {step.detail}")
                    body = step_to_latex(step)
                    if body:
                        parts.append("")
                        parts.append(f"   $$\n   {body}\n   $$")
                    parts.append("")
        return "\n".join(parts) + "\n"

    def html(self) -> str:
        blocks = []
        for i, sol in enumerate(self.solutions, 1):
            steps_html = []
            for step in sol.steps:
                body = step_to_latex(step)
                item = f"<strong>{step.title}</strong>"
                if step.detail:
                    item += f"<br><small>{step.detail}</small>"
                if body:
                    item += f"$$\n{body}\n$$"
                steps_html.append(f"<li>{item}</li>")
            steps_html = "\n".join(steps_html)
            blocks.append(
                f"<section>"
                f"<h2>{i}. {sol.title}</h2>"
                f"<p class=\"question\"><strong>Soru:</strong> {sol.question}<br>"
                f"<small>çözücü: <code>{sol.solver}</code></small></p>"
                f"<p class=\"result\"><strong>Sonuç:</strong> $${sol.result_tex}$$</p>"
                f"<ol class=\"steps\">{steps_html}</ol>"
                f"</section>"
            )
        body = "\n".join(blocks)
        footer = f"{len(self.solutions)} soru — {datetime.date.today().isoformat()}"
        return (
            self.HTML_TEMPLATE
            .replace("__TITLE__", self.title)
            .replace("__BODY__", body)
            .replace("__FOOTER__", footer)
        )

    def text(self) -> str:
        parts = [self.title, "=" * len(self.title), ""]
        for i, sol in enumerate(self.solutions, 1):
            parts.append(f"{i}) {sol.title}  [soruyu çözen: {sol.solver}]")
            parts.append(f"   Soru : {sol.question}")
            parts.append(f"   Sonuç: {sol.result_text}")
            for n, step in enumerate(sol.steps, 1):
                parts.append(f"   {n}. {step.title}")
                body = step_to_text(step)
                if body:
                    for line in body.splitlines():
                        parts.append(f"        {line}")
            parts.append("")
        return "\n".join(parts)

    def save_markdown(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.markdown(), encoding="utf-8")
        return path

    def save_html(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.html(), encoding="utf-8")
        return path

    def save_text(self, path: str | Path) -> Path:
        path = Path(path)
        path.write_text(self.text(), encoding="utf-8")
        return path
