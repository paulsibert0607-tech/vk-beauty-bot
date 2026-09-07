# -*- coding: utf-8 -*-
# main.py — VK-бот для салона красоты (запись клиентов)
import json
import re
import random
import requests
from datetime import datetime, timedelta
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import config

CATEGORIES = {
    "Стрижки": [
        {"id": 1, "name": "Женская стрижка", "price": 1500, "duration": 40, "masters": ["Алина", "Мария"]},
        {"id": 2, "name": "Мужская стрижка", "price": 1000, "duration": 30, "masters": ["Дмитрий", "Олег"]},
        {"id": 3, "name": "Детская стрижка", "price": 800, "duration": 30, "masters": ["Алина", "Мария"]},
    ],
    "Окрашивание": [
        {"id": 4, "name": "Окрашивание (однотонное)", "price": 3000, "duration": 120, "masters": ["Алина", "Мария"]},
        {"id": 5, "name": "Окрашивание (сложное)", "price": 5000, "duration": 180, "masters": ["Алина"]},
        {"id": 6, "name": "Мелирование", "price": 2500, "duration": 120, "masters": ["Мария"]},
    ],
    "Укладки": [
        {"id": 7, "name": "Укладка", "price": 1200, "duration": 45, "masters": ["Алина", "Мария", "Олег"]},
        {"id": 8, "name": "Ламинирование волос", "price": 2000, "duration": 60, "masters": ["Мария"]},
        {"id": 9, "name": "Кератин", "price": 4000, "duration": 150, "masters": ["Алина"]},
    ],
    "Ногти": [
        {"id": 10, "name": "Маникюр (классический)", "price": 1200, "duration": 60, "masters": ["Наталья", "Елена"]},
        {"id": 11, "name": "Маникюр (гель-лак)", "price": 1500, "duration": 75, "masters": ["Наталья", "Елена"]},
        {"id": 12, "name": "Педикюр", "price": 1800, "duration": 90, "masters": ["Наталья"]},
        {"id": 13, "name": "Наращивание ногтей", "price": 2200, "duration": 90, "masters": ["Елена"]},
    ],
    "Массаж": [
        {"id": 14, "name": "Массаж (спины)", "price": 2000, "duration": 60, "masters": ["Дмитрий"]},
        {"id": 15, "name": "Массаж (полный)", "price": 3500, "duration": 90, "masters": ["Дмитрий"]},
    ],
}

ALL_SERVICES = []
for cat_services in CATEGORIES.values():
    ALL_SERVICES.extend(cat_services)

FAQ = {
    "адрес": "ул. Чатботная, 1, 2 этаж.",
    "время": "ежедневно 09:00-20:00.",
    "оплата": "наличные, карта, СБП.",
    "скидки": "скидка 5% на первое посещение при записи через бота.",
    "перенос": "напишите нам, подберём новое время.",
    "отмена": "нажмите «Отменить» в меню или напишите нам.",
}

user_states = {}

def get_user(user_id):
    if user_id not in user_states:
        user_states[user_id] = {"step": "menu", "service": None, "master": None, "date": None, "time": None, "name": None, "phone": None, "category": None}
    return user_states[user_id]

def main_menu_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    kb.add_callback_button("Услуги", color=VkKeyboardColor.PRIMARY, payload={"type": "services"})
    kb.add_callback_button("Мои записи", color=VkKeyboardColor.SECONDARY, payload={"type": "my_bookings"})
    kb.add_line()
    kb.add_callback_button("Вопрос", color=VkKeyboardColor.SECONDARY, payload={"type": "faq"})
    kb.add_callback_button("Связаться", color=VkKeyboardColor.SECONDARY, payload={"type": "contact"})
    return kb

def categories_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    for cat in CATEGORIES:
        kb.add_callback_button(cat, color=VkKeyboardColor.PRIMARY, payload={"type": "category", "name": cat})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_menu"})
    return kb

def category_keyboard(category_name):
    kb = VkKeyboard(one_time=False, inline=True)
    services = CATEGORIES.get(category_name, [])
    for s in services:
        kb.add_callback_button(f"{s['name']} ({s['price']}p)", color=VkKeyboardColor.PRIMARY, payload={"type": "service", "id": s["id"]})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_categories"})
    return kb

def masters_keyboard(masters):
    kb = VkKeyboard(one_time=False, inline=True)
    for m in masters:
        kb.add_callback_button(m, color=VkKeyboardColor.PRIMARY, payload={"type": "master", "name": m})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_category"})
    return kb

def dates_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    today = datetime.now()
    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    for i in range(1, 8):
        d = today + timedelta(days=i)
        label = f"{d.day}.{d.month} ({days_ru[d.weekday()]})"
        if i % 2 == 0:
            kb.add_line()
        kb.add_callback_button(label, color=VkKeyboardColor.PRIMARY, payload={"type": "date", "date": d.strftime("%d.%m")})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_masters"})
    return kb

def times_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    hours = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00", "18:00", "19:00"]
    kb.add_callback_button(hours[0], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[0]})
    kb.add_callback_button(hours[1], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[1]})
    kb.add_line()
    kb.add_callback_button(hours[2], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[2]})
    kb.add_callback_button(hours[3], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[3]})
    kb.add_line()
    kb.add_callback_button(hours[4], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[4]})
    kb.add_callback_button(hours[5], color=VkKeyboardColor.PRIMARY, payload={"type": "time", "time": hours[5]})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_dates"})
    return kb

def confirm_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    kb.add_callback_button("Подтвердить", color=VkKeyboardColor.POSITIVE, payload={"type": "confirm"})
    kb.add_callback_button("Отменить", color=VkKeyboardColor.NEGATIVE, payload={"type": "cancel"})
    return kb

def faq_keyboard():
    kb = VkKeyboard(one_time=False, inline=True)
    kb.add_callback_button("Адрес", color=VkKeyboardColor.SECONDARY, payload={"type": "faq_answer", "key": "адрес"})
    kb.add_callback_button("Время работы", color=VkKeyboardColor.SECONDARY, payload={"type": "faq_answer", "key": "время"})
    kb.add_line()
    kb.add_callback_button("Оплата", color=VkKeyboardColor.SECONDARY, payload={"type": "faq_answer", "key": "оплата"})
    kb.add_callback_button("Скидки", color=VkKeyboardColor.SECONDARY, payload={"type": "faq_answer", "key": "скидки"})
    kb.add_line()
    kb.add_callback_button("Назад", color=VkKeyboardColor.SECONDARY, payload={"type": "back_menu"})
    return kb

def ai_reply(text):
    with open("system_prompt.md", "r", encoding="utf-8") as f:
        sys_prompt = f.read()
    with open("knowledge_base.md", "r", encoding="utf-8") as f:
        knowledge = f.read()
    full_prompt = f"{sys_prompt}\n\n=== БАЗА ЗНАНИЙ (используй только эти факты) ===\n{knowledge}\n\nОтвечай на вопрос, используя информацию из базы знаний. Если в базе нет ответа — вежливо предложи передать вопрос администратору."
    if not config.PROXY_API_KEY:
        return None
    try:
        resp = requests.post(
            f"{config.PROXY_API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {config.PROXY_API_KEY}", "Content-Type": "application/json"},
            json={"model": config.PROXY_MODEL, "messages": [{"role": "system", "content": full_prompt}, {"role": "user", "content": text}], "max_tokens": 150},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]
        else:
            print(f"[AI] HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[AI] Error: {e}")
    return None

def save_to_sheet(data):
    if not config.GOOGLE_SHEET_URL:
        print(f"[TABLE] {data}")
        return
    try:
        resp = requests.post(config.GOOGLE_SHEET_URL, json=data, timeout=10)
        if resp.status_code == 200:
            print(f"[TABLE] OK")
        else:
            print(f"[TABLE] HTTP {resp.status_code}")
    except Exception as e:
        print(f"[TABLE] Error: {e}")

def notify_admin(vk, text):
    if config.ADMIN_ID:
        try:
            vk.messages.send(user_id=config.ADMIN_ID, message=text, random_id=random.randint(1, 999999))
            print("[ADMIN] OK")
        except Exception as e:
            print(f"[ADMIN] Error: {e}")

def send(vk, user_id, message, keyboard=None):
    kw = {}
    if keyboard:
        kw["keyboard"] = keyboard.get_keyboard()
    vk.messages.send(user_id=user_id, message=message, random_id=random.randint(1, 999999), **kw)

def handle_text(vk, event):
    user_id = event.obj.message["from_id"]
    text = event.obj.message["text"].strip()
    user = get_user(user_id)

    if user["step"] == "waiting_name":
        if text.isdigit():
            send(vk, user_id, "Имя не может быть числом. Напишите ваше имя.")
            return
        if len(text) < 2:
            send(vk, user_id, "Имя слишком короткое.")
            return
        user["name"] = text
        user["step"] = "waiting_phone"
        send(vk, user_id, f"Отлично, {text}! Теперь введите номер телефона (11 цифр):")
        return

    if user["step"] == "waiting_phone":
        digits = re.sub(r"\D", "", text)
        if len(digits) != 11:
            send(vk, user_id, "Нужно ровно 11 цифр (например 79001234567). Попробуйте ещё раз:")
            return
        user["phone"] = digits
        user["step"] = "confirm"
        s = user.get("service")
        if not s or not user.get("master") or not user.get("date") or not user.get("time") or not user.get("name"):
            user_states.pop(user_id, None)
            send(vk, user_id, "Данные записи потеряны. Начните заново.", main_menu_keyboard())
            return
        summary = (
            f"Сводка записи:\n"
            f"Услуга: {s['name']} - {s['price']} p\n"
            f"Мастер: {user['master']}\n"
            f"Дата: {user['date']}\n"
            f"Время: {user['time']}\n"
            f"Имя: {user['name']}\n"
            f"Телефон: {user['phone']}\n\n"
            f"Подтвердить запись?"
        )
        send(vk, user_id, summary, confirm_keyboard())
        return

    if user["step"] == "menu":
        ai = ai_reply(text)
        if ai:
            send(vk, user_id, ai, main_menu_keyboard())
        else:
            send(vk, user_id, "Выберите действие в меню:", main_menu_keyboard())
        return

    send(vk, user_id, "Используйте кнопки. Напишите «назад» для главного меню.")

def handle_callback(vk, event):
    user_id = event.obj.user_id
    payload = event.object.get("payload", {})
    action = payload.get("type")
    user = get_user(user_id)

    try:
        vk.messages.sendMessageEventAnswer(
            user_id=user_id,
            event_id=event.object.get("event_id", ""),
            peer_id=event.obj.get("peer_id", user_id),
            event_data=json.dumps({"type": "show_snackbar", "text": "Обрабатываю..."}),
        )
    except Exception:
        pass

    if action == "back_menu":
        user["step"] = "menu"
        send(vk, user_id, "Главное меню:", main_menu_keyboard())

    elif action == "services":
        user["step"] = "choose_category"
        send(vk, user_id, "Выберите категорию:", categories_keyboard())

    elif action == "category":
        cat_name = payload.get("name", "")
        user["step"] = "choose_service"
        user["category"] = cat_name
        send(vk, user_id, f"{cat_name}:", category_keyboard(cat_name))

    elif action == "back_categories":
        user["step"] = "choose_category"
        send(vk, user_id, "Выберите категорию:", categories_keyboard())

    elif action == "service":
        service_id = payload.get("id")
        service = next((s for s in ALL_SERVICES if s["id"] == service_id), None)
        if service:
            user["service"] = service
            user["step"] = "choose_master"
            send(vk, user_id, f"{service['name']} - {service['price']} p ({service['duration']} мин)\n\nВыберите мастера:", masters_keyboard(service["masters"]))

    elif action == "back_masters":
        if user["service"]:
            user["step"] = "choose_master"
            send(vk, user_id, "Выберите мастера:", masters_keyboard(user["service"]["masters"]))

    elif action == "back_category":
        cat_name = user.get("category", "")
        if cat_name:
            user["step"] = "choose_service"
            send(vk, user_id, f"{cat_name}:", category_keyboard(cat_name))

    elif action == "master":
        user["master"] = payload.get("name")
        user["step"] = "choose_date"
        send(vk, user_id, f"Мастер: {user['master']}\n\nВыберите дату:", dates_keyboard())

    elif action == "back_dates":
        user["step"] = "choose_date"
        send(vk, user_id, "Выберите дату:", dates_keyboard())

    elif action == "date":
        user["date"] = payload.get("date")
        user["step"] = "choose_time"
        send(vk, user_id, f"Дата: {user['date']}\n\nВыберите время:", times_keyboard())

    elif action == "time":
        user["time"] = payload.get("time")
        user["step"] = "waiting_name"
        send(vk, user_id, f"Дата и время: {user['date']} в {user['time']}\n\nВведите ваше имя:")

    elif action == "confirm":
        s = user["service"]
        record = {"service": s["name"], "price": s["price"], "master": user["master"], "date": user["date"], "time": user["time"], "name": user["name"], "phone": user["phone"], "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M")}
        save_to_sheet(record)
        notify_admin(vk, f"Новая запись!\n{s['name']}\n{user['master']}\n{user['date']} в {user['time']}\n{user['name']}\n{user['phone']}")
        send(vk, user_id, f"Спасибо, {user['name']}! Запись принята.\n\nЖдём вас {user['date']} в {user['time']}.\nАдрес: ул. Чатботная, 1.\n\nЕсли нужно перенести - напишите нам.", main_menu_keyboard())
        user_states.pop(user_id, None)

    elif action == "cancel":
        user_states.pop(user_id, None)
        send(vk, user_id, "Запись отменена. Можете записаться позже.", main_menu_keyboard())

    elif action == "faq":
        user["step"] = "faq"
        send(vk, user_id, "Что хотите узнать?", faq_keyboard())

    elif action == "faq_answer":
        key = payload.get("key", "")
        answer = FAQ.get(key, "Уточните у администратора.")
        send(vk, user_id, answer, faq_keyboard())

    elif action == "my_bookings":
        send(vk, user_id, "Пока у вас нет записей. Запишитесь через «Услуги»!", main_menu_keyboard())

    elif action == "contact":
        send(vk, user_id, "По вопросам пишите администратору:\nVK: @admin\nТелефон: +7 (900) 123-45-67", main_menu_keyboard())

def main():
    print("=" * 50)
    print("Bot Strana Chatbotiya starting...")
    print(f"Group ID: {config.VK_GROUP_ID}")
    print("=" * 50)

    vk_session = vk_api.VkApi(token=config.VK_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, config.VK_GROUP_ID)
    print("Listening for messages... (Ctrl+C to stop)")

    for event in longpoll.listen():
        try:
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                user_id = msg["from_id"]
                if user_id < 0:
                    continue
                text = msg.get("text", "").strip().lower()
                if text in ("назад", "start", "menu", "меню", "/start"):
                    user_states.pop(user_id, None)
                    send(vk, user_id, "Добро пожаловать в салон красоты!\nПомогу записаться на услугу.", main_menu_keyboard())
                    continue
                handle_text(vk, event)
            elif event.type == VkBotEventType.MESSAGE_EVENT:
                handle_callback(vk, event)
        except Exception as e:
            print(f"[ERROR] {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")