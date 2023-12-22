from typing import List

import database
from telebot import types


def create_menu_text(user_id: int, db: database.DataBase) -> str:
    user = db.get_user(user_id)

    if len(user["ingredients"]) == 0:
        return (f"{user['name']}, ты в главном меню.\n\n"
                "Нажми кнопку \"Добавить ингредиент 🥕\", чтобы начать.")

    text = "Список текущих ингредиентов:\n\n"

    for i, item in enumerate(user["ingredients"]):
        text += f"{i + 1}. {item}\n"

    text += "\n"
    text += "Нажми кнопку \"Найти рецепт 🍳\", чтобы я начал искать рецепты по этим ингредиентам."

    return text


def create_menu_kb(user_id: int, db: database.DataBase) -> types.InlineKeyboardMarkup:
    user = db.get_user(user_id)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="Добавить ингредиент 🥕", callback_data=f"add"))

    if len(user["ingredients"]) == 0:
        return kb

    kb.add(types.InlineKeyboardButton(text="Удалить ингредиент ❌", callback_data=f"delete"))
    kb.add(types.InlineKeyboardButton(text="Найти рецепт 🍳", callback_data=f"find"))

    return kb


def create_add_text(user_id: int, db: database.DataBase) -> str:
    user = db.get_user(user_id)

    if len(user["ingredients"]) == 0:
        return "Напиши мне название ингредиента, а я добавлю его в твой список 📜"

    text = ("Напиши мне название ингредиента, а я добавлю его в твой список 📜\n\n"
            "Текущие ингредиенты:\n\n")

    for i, item in enumerate(user["ingredients"]):
        text += f"{i + 1}. {item}\n"

    text += "\n"
    text += "Как закончишь, жми кнопку \"Готово ✅\""

    return text


def create_delete_kb(user_id: int, db: database.DataBase) -> types.InlineKeyboardMarkup:
    user = db.get_user(user_id)

    kb = types.InlineKeyboardMarkup(row_width=1)

    for i, item in enumerate(user["ingredients"]):
        kb.add(types.InlineKeyboardButton(text=item, callback_data=f"remove_{i}"))

    kb.add(types.InlineKeyboardButton(text="Готово ✅", callback_data=f"ready"))

    return kb


def create_possible_kb(words: List[str]) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)

    for item in words:
        kb.add(types.InlineKeyboardButton(text=item, callback_data=f"add_{item}"))

    kb.add(types.InlineKeyboardButton(text="Тут нет моего ингредиента", callback_data=f"ready"))

    return kb


def create_recipy_text(recipy: dict) -> str:
    text = f"<b>{recipy['name']}</b>\n\n"
    text += f"{recipy['desc']}\n\n"
    text += "Ингредиенты:\n\n"
    for ing in recipy['ingredients']:
        text += f"- {ing}\n"

    text += f"\n<i>Рецепт по ссылке:</i> {recipy['link']}"

    return text
