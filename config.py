# -*- coding: utf-8 -*-
# config.py — настройки из .env
import os
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = int(os.getenv("VK_GROUP_ID", "0"))
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
PROXY_API_BASE = os.getenv("PROXY_API_BASE", "https://api.proxyapi.ru/openai/v1")
PROXY_MODEL = os.getenv("PROXY_MODEL", "gpt-4o-mini")
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))