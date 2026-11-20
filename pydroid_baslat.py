#!/usr/bin/env python3
"""Pydroid 3 başlatıcısı: IDE'de ▶ ile çalıştır, soru yaz, render edilmiş resim al.

Terminal gerektirmez: Pydroid 3'te bu dosyayı açıp ▶ düğmesine bas.
Soruları `soru>` penceresine yaz; her çözüm hem deftere kopyalanabilir
LaTeX blokları hem de formülleri çizilmiş PNG resim olarak üretilir.
Resmi telefonda Galeri/Görseller'den açıp defterine bakarak yazabilirsin.
`çıkış` yazınca tüm çözümler defter.md / defter.html / defter.txt olarak
ve PNG'ler defter_resim/ klasörüne kaydedilir.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathpad import MathPad, Notebook, NoSolverFound, SolverError

EXIT_WORDS = {"çıkış", "cikis", "exit", "quit", "q"}


def main() -> int:
    from mathpad.cli import _print_latex

    base = os.path.dirname(os.path.abspath(__file__))
    png_dir = os.path.join(base, "defter_resim")
    try:
        import matplotlib  # noqa: F401

        png_ok = True
    except ImportError:
        png_ok = False
        print("Not: matplotlib kurulu değil; PNG resim üretilemeyecek.")
        print("PNG için Pydroid Pip menüsünden 'matplotlib' kur.")

    engine = MathPad()
    notebook = Notebook(title="Pydroid Defteri")
    failures = 0
    solved = 0

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
            solved += 1
            _print_latex(solution, notebook_mode=False)
            if png_ok:
                try:
                    from mathpad.rendering.png import save_solution_png

                    path = save_solution_png(solution, png_dir, solved)
                    print(f"📷 resim: {path}")
                except Exception as exc:
                    print(f"(resim üretilemedi: {exc})")
        except (NoSolverFound, SolverError, ValueError) as exc:
            failures += 1
            print(f"hata: {exc}")


    print("\n" + "=" * 50)
    print(f"defter: {notebook.save_markdown(os.path.join(base, 'defter.md'))}")
    print(f"html:   {notebook.save_html(os.path.join(base, 'defter.html'))}")
    print(f"metin:  {notebook.save_text(os.path.join(base, 'defter.txt'))}")
    if failures:
        print(f"({failures} soru çözülemedi)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
