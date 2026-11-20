#!/usr/bin/env python3
"""Pydroid 3 başlatıcısı: IDE'de ▶ ile çalıştır, soru yaz, LaTeX al.

Terminal gerektirmez: Pydroid 3'te bu dosyayı açıp ▶ düğmesine bas.
Soruları `soru>` penceresine yaz; her çözüm deftere kopyalanabilir
LaTeX blokları halinde çıktı penceresine yazılır. `çıkış` yazınca
oturumdaki tüm çözümler defter.md / defter.html / defter.txt olarak
bu dosyanın yanına kaydedilir.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathpad import MathPad, Notebook, NoSolverFound, SolverError

EXIT_WORDS = {"çıkış", "cikis", "exit", "quit", "q"}


def main() -> int:
    from mathpad.cli import _print_latex

    engine = MathPad()
    notebook = Notebook(title="Pydroid Defteri")
    failures = 0

    print("=" * 50)
    print("MathPad'e hoş geldin!")
    print("Soruyu yaz, ENTER'a bas. Çıkmak için: çıkış")
    print("=" * 50)

    while True:
        try:
            question = input("\nsoru> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in EXIT_WORDS:
            break
        try:
            solution = engine.ask(question)
            notebook.add(solution)
            _print_latex(solution)
        except (NoSolverFound, SolverError, ValueError) as exc:
            failures += 1
            print(f"hata: {exc}")

    base = os.path.dirname(os.path.abspath(__file__))
    print("\n" + "=" * 50)
    print(f"defter: {notebook.save_markdown(os.path.join(base, 'defter.md'))}")
    print(f"html:   {notebook.save_html(os.path.join(base, 'defter.html'))}")
    print(f"metin:  {notebook.save_text(os.path.join(base, 'defter.txt'))}")
    if failures:
        print(f"({failures} soru çözülemedi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
