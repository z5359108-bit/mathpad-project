#!/usr/bin/env python3
"""Pydroid 3 başlatıcısı: bu dosyayı açıp ▶ bas, MathPad ana menüsü açılır.

Tüm yönetim menü içinden yapılır: soru çözme, defter kaydetme,
çıktı biçimi (LaTeX / render edilmiş PNG resim) ve ayarlar.
Terminal kullanmak istersen: python mathpad_menu.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mathpad_menu import main

if __name__ == "__main__":
    sys.exit(main())
