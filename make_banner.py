# -*- coding: utf-8 -*-
"""Создание баннера чат-бота 'Страна Чатботия' в бренд-стиле."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banner.png")

W, H = 1200, 400
img = Image.new("RGB", (W, H), "#0f172a")
d = ImageDraw.Draw(img)

# градиент фон (фиолетовый -> тёмный)
for y in range(H):
    t = y / H
    r = int(15 + (139 - 15) * t * 0.55)
    g = int(23 + (92 - 23) * t * 0.55)
    b = int(42 + (246 - 42) * t * 0.55)
    d.line([(0, y), (W, y)], fill=(r, g, b))

# нижняя линия-акцент
d.rectangle([0, H - 8, W, H], fill="#2563eb")

def font(size):
    for p in ["C:/Windows/Fonts/msgothic.ttc", "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"]:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

f_big = font(52)
f_mid = font(30)
f_small = font(22)

# заголовок
d.text((80, 60), "Страна Чатботия", fill="#e2e8f0", font=f_big)
d.text((80, 150), "Чат-бот для записи в салон красоты", fill="#94a3b8", font=f_mid)
d.text((80, 230), "ВКонтакте  ·  услуги, цены, мастера  ·  ИИ-агент", fill="#c4b5fd", font=f_mid)
d.text((80, 320), "сделано на vibe-кодинге — быстро и точечно", fill="#64748b", font=f_small)

img.save(OUT)
print("OK:", OUT)