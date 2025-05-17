#!/bin/bash

# 1. Suorita Magick + Tesseract OCR ja tallenna tekstitiedostoon
magick x: -modulate 100,0 -resize 400% -set density 300 png:- > ocr_output.png

# 2. Aja Python-skripti (esimerkiksi "analyysi.py")
gpt4arm-env/bin/python combined_sricpt.py
