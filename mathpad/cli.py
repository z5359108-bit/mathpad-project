"""Komut satırı arayüzü: tek soru, interaktif REPL, defter çıktısı."""

from __future__ import annotations

import argparse
import sys

from .engine import MathPad, NoSolverFound, SolverError
from .notebook import Notebook
from .solvers import DEFAULT_SOLVERS


def _print_latex(solution, notebook_mode: bool = True) -> None:
    from .rendering.latex import step_to_latex

    if notebook_mode:
        print("% --- LaTeX çıktısı (defterine kopyala) ---")
    print(f"\\textbf{{Soru:}} {solution.question}\\\\")
    print("$$")
    print(f"\\text{{{solution.title}}}: {solution.result_tex}")
    print("$$")
    print("\\begin{itemize}")
    for step in solution.steps:
        body = step_to_latex(step)
        if body:
            print(f"  \\item \\textbf{{{step.title}}}: $$ {body} $$")
        else:
            print(f"  \\item \\textbf{{{step.title}}}")
    print("\\end{itemize}")


def _print_solution(solution) -> None:
    from .rendering.text import step_to_text

    print(f"\n[çözücü: {solution.solver}]")
    for n, step in enumerate(solution.steps, 1):
        print(f"  {n}. {step.title}")
        body = step_to_text(step)
        if body:
            for line in body.splitlines():
                print(f"     {line}")
        if step.detail:
            print(f"     ({step.detail})")
    print(f"\n  ⟹ SONUÇ: {solution.result_text}\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mathpad", description="Modüler matematik çözücü")
    parser.add_argument("question", nargs="*", help="Çözülecek soru")
    parser.add_argument("-n", "--notebook", metavar="DOSYA", help="LaTeX'li Markdown defter yolu")
    parser.add_argument("--html", metavar="DOSYA", help="MathJax'lı HTML defter yolu")
    parser.add_argument("--text", metavar="DOSYA", help="Düz metin defter yolu")
    parser.add_argument("-s", "--solver", help="Zorla kullanılacak çözücü adı")
    parser.add_argument("-p", "--pretty", action="store_true", help="LaTeX yerine unicode okunabilir çıktı")
    parser.add_argument("--defter", action="store_true", help="Kısa defter zinciri: sadece matematik, açıklama ve ondalık yok")
    parser.add_argument("--png", metavar="KLASÖR", help="Her çözümü render edilmiş PNG resim olarak bu klasöre kaydet")
    parser.add_argument("--list", action="store_true", help="Kayıtlı çözücüleri listele")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    engine = MathPad()
    if args.list:
        for solver in engine.solvers:
            print(f"{solver.name:16s} {solver.title}")
        return 0
    if args.solver:
        named = {s.name: s for s in DEFAULT_SOLVERS}
        if args.solver not in named:
            print(f"Bilinmeyen çözücü: {args.solver}\nMevcut: {', '.join(named)}", file=sys.stderr)
            return 2
        engine = MathPad(solvers=(named[args.solver],), threshold=0.0)

    notebook = Notebook()
    interactive = not args.question
    if interactive:
        print("MathPad'e hoş geldin. Soru yaz ('çıkış' ile çıkar).")
        print("=" * 50)

    failures = 0
    solved = 0
    questions = iter([" ".join(args.question)])

    while True:
        try:
            if interactive:
                try:
                    question = input("soru> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print()
                    break
                if not question:
                    continue
                if question.lower() in {"çıkış", "cikis", "exit", "quit", "q"}:
                    break
            else:
                try:
                    question = next(questions).strip()
                except StopIteration:
                    break
                if not question:
                    break

            try:
                if args.solver:
                    solution = engine.solvers[0].solve(question)
                    engine.history.append(solution)
                else:
                    solution = engine.ask(question)
                notebook.add(solution)
                solved += 1
                if args.defter:
                    from .rendering.defter import defter_metni

                    print(defter_metni(solution))
                elif args.pretty:
                    if interactive:
                        _print_solution(solution)
                    else:
                        print(f"[{solution.solver}] {solution.title}: {solution.result_text}")
                else:
                    _print_latex(solution)
                if args.png:
                    from .rendering.png import save_solution_png
                    print(f"resim: {save_solution_png(solution, args.png, solved)}")
            except (NoSolverFound, SolverError, ValueError) as exc:
                failures += 1
                print(f"hata: {exc}", file=sys.stderr)
        except Exception:
            failures += 1
            break

    if args.notebook:
        print(f"Defter: {notebook.save_markdown(args.notebook)}")
    if args.html:
        print(f"HTML:   {notebook.save_html(args.html)}")
    if args.text:
        print(f"Metin:  {notebook.save_text(args.text)}")
    if interactive and failures:
        print(f"({failures} soru çözülemedi)")
    exit_code = 0 if interactive or failures == 0 else 1
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
