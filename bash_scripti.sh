#!/bin/bash

# 1. Suorita Magick + Tesseract OCR ja tallenna tekstitiedostoon
convert x: -modulate 100,0 -resize 400% -set density 300 png:- > ocr_output.png

# 2. Aja Python-skripti (esimerkiksi "analyysi.py")
sudo venv/bin/python test.py
