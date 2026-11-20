#!/usr/bin/env python3
"""MathPad ana menü: araç, komut satırı olmadan bu menüden yönetilir.

Pydroid 3'te bu dosyayı açıp ▶ düğmesine bas; terminalde
`python mathpad_menu.py` yazarak da kullanabilirsin.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathpad import MathPad, Notebook, NoSolverFound, SolverError
from mathpad.settings import Settings

BASE = os.path.dirname(os.path.abspath(__file__))
AYAR_DOSYASI = os.path.join(BASE, "ayarlar.json")

EXIT_WORDS = {"çıkış", "cikis", "exit", "quit", "q"}


def _temizle() -> None:
    print("\n" + "=" * 56)


def _cizgi() -> None:
    print("-" * 56)


class App:
    def __init__(self) -> None:
        self.ayar = Settings.load(AYAR_DOSYASI)
        self.engine = MathPad()
        self.notebook = Notebook(title="MathPad Defteri")
        self.png_sayac = 0

    # ---------- soru çözme ----------

    def _resim_uret(self, solution, ad: str) -> str | None:
        try:
            from mathpad.rendering.png import solution_to_png

            klasor = os.path.join(BASE, self.ayar.png_klasor)
            self.png_sayac += 1
            path = os.path.join(klasor, f"{ad}_{self.png_sayac:03d}.png")
            solution_to_png(solution, path, dpi=self.ayar.dpi)
            return path
        except Exception as exc:
            print(f"(resim üretilemedi: {exc})")
            return None

    def _cozum_goster(self, solution) -> None:
        """Çözümü seçili çıktı ayarına göre göster."""
        from mathpad.cli import _print_latex, _print_solution

        mode = self.ayar.cikti
        if mode == "pretty":
            _print_solution(solution)
        elif mode == "png":
            path = self._resim_uret(solution, "soru")
            if path:
                print(f"📷 Formüller render edildi: {path}")
                print("   Resmi aç, defterine bakarak yazabilirsin.")
        else:
            if self.ayar.latex_etkin:
                _print_latex(solution, notebook_mode=False)
                if mode == "ikisi":
                    path = self._resim_uret(solution, "soru")
                    if path:
                        print(f"📷 Ayrıca resim: {path}")

    def soru_sor(self) -> None:
        _cizgi()
        question = input("Soru (boş bırakırsan menuye dönersin): ").strip()
        if not question:
            return
        try:
            solution = self.engine.ask(question)
            self.notebook.add(solution)
            print()
            self._cozum_goster(solution)
            _cizgi()
            print("Çözüm defterine eklendi. (Menü 3'ten defteri kaydedebilirsin)")
        except (NoSolverFound, SolverError, ValueError) as exc:
            print(f"hata: {exc}")

    def serbest_mod(self) -> None:
        _cizgi()
        print("Serbest mod: soru yaz, ENTER'a bas. 'menu' ya da 'çıkış' ile dön.")
        _cizgi()
        while True:
            try:
                question = input("soru> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not question:
                continue
            if question.lower() in EXIT_WORDS or question.lower() == "menu":
                break
            try:
                solution = self.engine.ask(question)
                self.notebook.add(solution)
                print()
                self._cozum_goster(solution)
            except (NoSolverFound, SolverError, ValueError) as exc:
                print(f"hata: {exc}")

    # ---------- defter ----------

    def defter_menu(self) -> None:
        while True:
            _cizgi()
            print(f"📋 DEFTER — {len(self.notebook.solutions)} çözüm kayıtlı")
            _cizgi()
            print("  1) Markdown defteri kaydet (.md, LaTeX'li)")
            print("  2) HTML defteri kaydet (.html, MathJax: tarayıcıda güzel formüller)")
            print("  3) Düz metin kaydet (.txt)")
            print("  4) Tüm çözümleri PNG resimlere döktür")
            print("  5) Çözümleri ekranda listele")
            print("  0) Menüye dön")
            secim = input("seçim> ").strip()
            if secim == "1":
                print(self.notebook.save_markdown(self._dosya("md")))
            elif secim == "2":
                print(self.notebook.save_html(self._dosya("html")))
            elif secim == "3":
                print(self.notebook.save_text(self._dosya("txt")))
            elif secim == "4":
                self._tum_resimler()
            elif secim == "5":
                self._cozumleri_listele()
            elif secim == "0" or secim.lower() in EXIT_WORDS:
                return

    def _dosya(self, uzanti: str) -> str:
        return os.path.join(BASE, f"{self.ayar.defter_adi}.{uzanti}")

    def _tum_resimler(self) -> None:
        if not self.notebook.solutions:
            print("(defter boş)")
            return
        klasor = os.path.join(BASE, self.ayar.png_klasor)
        try:
            from mathpad.rendering.png import solution_to_png
        except ImportError:
            print("matplotlib kurulu değil (Pydroid Pip menüsünden kur).")
            return
        for i, solution in enumerate(self.notebook.solutions, 1):
            path = os.path.join(klasor, f"defter_{i:03d}.png")
            try:
                solution_to_png(solution, path, dpi=self.ayar.dpi)
                print(f"📷 {path}")
            except Exception as exc:
                print(f"(üretilemedi {path}: {exc})")

    def _cozumleri_listele(self) -> None:
        if not self.notebook.solutions:
            print("(defter boş)")
            return
        for i, solution in enumerate(self.notebook.solutions, 1):
            print(f"[{i}] {solution.question}")
            print(f"    → {solution.title}: {solution.result_text}")

    # ---------- ayarlar ----------

    def ayarlar_menu(self) -> None:
        while True:
            _cizgi()
            print("⚙️  AYARLAR (değişiklik anında kaydedilir)")
            _cizgi()
            print(f"  1) Çıktı biçimi   : {self.ayar.cikti}")
            print(f"  2) PNG kalitesi   : {self.ayar.dpi} DPI")
            print(f"  3) PNG klasörü    : {self.ayar.png_klasor}")
            print(f"  4) Defter adı     : {self.ayar.defter_adi}")
            print("  5) Ayarları sıfırla")
            print("  0) Menüye dön")
            secim = input("seçim> ").strip()
            if secim == "1":
                self._cikti_degistir()
            elif secim == "2":
                self._sayi_degistir("Yeni DPI (72-400)", 72, 400, "dpi")
            elif secim == "3":
                deger = input("Klasör adı: ").strip()
                if deger and not any(c in deger for c in "/\\"):
                    self.ayar.png_klasor = deger
                    self._kaydet()
            elif secim == "4":
                deger = input("Defter dosya adı (uzantısız): ").strip()
                if deger and not any(c in deger for c in "/\\ "):
                    self.ayar.defter_adi = deger
                    self._kaydet()
            elif secim == "5":
                self.ayar = Settings()
                self._kaydet()
                print("Ayarlar varsayılana döndürüldü.")
            elif secim == "0" or secim.lower() in EXIT_WORDS:
                return

    def _cikti_degistir(self) -> None:
        print("  1) latex  — deftere kopyalanabilir LaTeX blokları")
        print("  2) png    — formülleri çizilmiş resim (defterime bakarak yazacağım)")
        print("  3) ikisi  — LaTeX + resim")
        print("  4) pretty — terminalde okunabilir unicode (derste değil, hızlı bakış)")
        secim = input("seçim> ").strip()
        haritalar = {"1": "latex", "2": "png", "3": "ikisi", "4": "pretty"}
        if secim in haritalar:
            self.ayar.cikti = haritalar[secim]
            self._kaydet()
            print(f"Çıktı biçimi: {self.ayar.cikti}")
        else:
            self.ayar.cikti = secim if secim in haritalar.values() else self.ayar.cikti
            self._kaydet()

    def _sayi_degistir(self, mesaj: str, alt: int, ust: int, alan: str) -> None:
        try:
            deger = int(input(f"{mesaj}: ").strip())
        except ValueError:
            print("Geçersiz sayı.")
            return
        deger = max(alt, min(ust, deger))
        setattr(self.ayar, alan, deger)
        self._kaydet()
        print(f"{alan} = {deger}")

    def _kaydet(self) -> None:
        self.ayar.gecerli()
        try:
            self.ayar.save(AYAR_DOSYASI)
        except OSError as exc:
            print(f"(ayar kaydedilemedi: {exc})")

    # ---------- diğer ----------

    def cozuculeri_listele(self) -> None:
        _cizgi()
        print("🧠 Kayıtlı çözücüler (motor en uygun olanı seçer)")
        _cizgi()
        for solver in self.engine.solvers:
            print(f"  {solver.name:16s} {solver.title}")

    def ornek_sorular(self) -> None:
        ornekler = [
            "x^2 - 3x + 2 = 0",
            "integral of x^2 from 0 to 3",
            "d/dx sin(x)*exp(x)",
            "[[1,2],[3,4]] matrisinin determinantı",
            "360 sayısını asal çarpanlarına ayır",
            "varyans [2, 4, 4, 4, 5, 5, 7, 9]",
        ]
        _cizgi()
        print("Örnek sorular çözülüp defterine eklenecek:")
        for i, s in enumerate(ornekler, 1):
            print(f"  {i}) {s}")
        secim = input("Hangisi? (numara, hepsi için 'h', iptal için ENTER): ").strip()
        if not secim:
            return
        hedefler = list(enumerate(ornekler, 1)) if secim.lower() == "h" else []
        if not hedefler and secim.isdigit() and 1 <= int(secim) <= len(ornekler):
            hedefler = [(int(secim), ornekler[int(secim) - 1])]
        for _, soru in hedefler:
            try:
                solution = self.engine.ask(soru)
                self.notebook.add(solution)
                print(f"\n[✓] {soru}")
                self._cozum_goster(solution)
            except (NoSolverFound, SolverError, ValueError) as exc:
                print(f"hata ({soru}): {exc}")

    def oturumu_kaydet(self) -> None:
        if not self.notebook.solutions:
            return
        print()
        _cizgi()
        print(f"Oturumdaki {len(self.notebook.solutions)} çözüm kaydediliyor…")
        print(f"  md  : {self.notebook.save_markdown(self._dosya('md'))}")
        print(f"  html: {self.notebook.save_html(self._dosya('html'))}")
        print(f"  txt : {self.notebook.save_text(self._dosya('txt'))}")

    # ---------- ana döngü ----------

    def run(self) -> int:
        print("=" * 56)
        print("  MathPad v1.1 — Akıllı Matematik Defteri")
        print("=" * 56)
        print(f"Çıktı biçimi: {self.ayar.cikti}   (Ayarlardan değiştir)")
        while True:
            _cizgi()
            print("  1) Soru çöz")
            print("  2) Serbest mod (art arda soru)")
            print("  3) Defterim (kaydet / listele / PNG döktür)")
            print("  4) Ayarlar (çıktı biçimi, PNG kalitesi…)")
            print("  5) Örnek sorular")
            print("  6) Çözücüleri listele")
            print("  0) Çıkış (oturumu deftere kaydeder)")
            try:
                secim = input("seçim> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                secim = "0"
            if secim == "1":
                self.soru_sor()
            elif secim == "2":
                self.serbest_mod()
            elif secim == "3":
                self.defter_menu()
            elif secim == "4":
                self.ayarlar_menu()
            elif secim == "5":
                self.ornek_sorular()
            elif secim == "6":
                self.cozuculeri_listele()
            elif secim == "0" or secim.lower() in EXIT_WORDS:
                self.oturumu_kaydet()
                print("\nGörüşürüz! 📚")
                return 0


def main() -> int:
    return App().run()


if __name__ == "__main__":
    sys.exit(main())
