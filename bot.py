import telebot
from telebot import types
from database import DataBase
from stages import Stages
import config
from recipy_manager import RecipyManager
from bot_utils import (create_menu_kb, create_menu_text, create_add_text, create_delete_kb, create_possible_kb,
                       create_recipy_text)
import sys

bot = telebot.TeleBot(config.BOT_TOKEN)
db = DataBase(config.DB_CACHE_PATH, config.DB_LOGGING, config.DB_SAVE_ITER)
rm = RecipyManager(logging=True)


@bot.message_handler(commands=["start"])
def handle_start(message):
    chat_id = message.chat.id

    db.create_user(chat_id, message.from_user.first_name)
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="Начать!", callback_data=f"start"))

    msg = bot.send_message(chat_id, f"Привет, {message.from_user.first_name} 👋!\n\n"
                                    f"Я бот, который поможет найти тебе рецепты из имеющихся у тебя ингредиентов 🥕.\n\n"
                                    f"Чтобы начать, нажми на кнопку снизу 😌",
                           reply_markup=kb)

    db.set_msg_id(chat_id, msg.id)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    stage = db.get_stage(chat_id)

    if stage != Stages.ADDING.value:
        bot.send_message(chat_id, "Я тебя не понимаю :(\n\n"
                                  "Если запутался, напиши команду /start")
        return

    words = rm.find_nearest(message.text.capitalize())

    if len(words) == 0:
        bot.send_message(chat_id, "Я не знаю такого ингредиента :(")
        return

    # Проверяем, возможно мы уже нашли идеально подходящее слово
    for w in words:
        if message.text.lower() == w.lower():
            db.add_ingredient(chat_id, message.text.capitalize())
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(text="Готово ✅", callback_data=f"ready"))

            msg_id = db.get_msg_id(chat_id)

            msg = bot.send_message(chat_id=chat_id, text=create_add_text(chat_id, db),
                                   reply_markup=kb)
            db.set_msg_id(chat_id, msg.id)

            if msg_id != -1:
                bot.delete_message(chat_id=chat_id, message_id=msg_id)
            return

    # Если нет, предлагаем пользователю выбрать
    msg_id = db.get_msg_id(chat_id)

    msg = bot.send_message(chat_id, text="Возможно ты имел ввиду какие-то из этих ингредиентов?",
                           reply_markup=create_possible_kb(words))

    db.set_msg_id(chat_id, msg.id)

    if msg_id != -1:
        try:
            bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception as e:
            print(f"Problem while deleting message: {str(e)} ", file=sys.stderr)


@bot.callback_query_handler(func=lambda call: True)
def handle_start(call):
    chat_id = call.message.chat.id
    msg_id = call.message.id

    if call.data in ["start", "ready"]:
        db.set_stage(chat_id, Stages.MENU.value)
        bot.edit_message_text(chat_id=chat_id, text=create_menu_text(chat_id, db),
                              reply_markup=create_menu_kb(chat_id, db), message_id=msg_id)

    elif call.data == "add":
        db.set_stage(chat_id, Stages.ADDING.value)
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(types.InlineKeyboardButton(text="Готово ✅", callback_data=f"ready"))
        bot.edit_message_text(chat_id=chat_id, text=create_add_text(chat_id, db),
                              reply_markup=kb, message_id=msg_id)

    elif call.data == "final":
        db.set_stage(chat_id, Stages.MENU.value)
        bot.delete_message(chat_id=chat_id, message_id=msg_id)
        bot.send_message(chat_id=chat_id, text=create_menu_text(chat_id, db),
                         reply_markup=create_menu_kb(chat_id, db))

    elif call.data == "delete":
        db.set_stage(chat_id, Stages.DELETE.value)
        bot.edit_message_text(chat_id=chat_id, text="Выбери ингредиент, который хочешь удалить",
                              reply_markup=create_delete_kb(chat_id, db), message_id=msg_id)

    elif call.data.startswith("remove"):
        _, index = call.data.split("_")
        index = int(index)
        length = db.pop_ingredient(chat_id, index)

        if length > 0:
            db.set_stage(chat_id, Stages.DELETE.value)
            bot.edit_message_text(chat_id=chat_id, text="Выбери ингредиент, который хочешь удалить",
                                  reply_markup=create_delete_kb(chat_id, db), message_id=msg_id)
        else:
            db.set_stage(chat_id, Stages.MENU.value)
            bot.edit_message_text(chat_id=chat_id, text=create_menu_text(chat_id, db),
                                  reply_markup=create_menu_kb(chat_id, db), message_id=msg_id)

    elif call.data.startswith("add"):
        _, name = call.data.split("_")
        db.add_ingredient(chat_id, name)
        db.set_stage(chat_id, Stages.MENU.value)
        bot.edit_message_text(chat_id=chat_id, text=create_menu_text(chat_id, db),
                              reply_markup=create_menu_kb(chat_id, db), message_id=msg_id)

    elif call.data == "find":
        user = db.get_user(chat_id)
        bot.edit_message_text(chat_id=chat_id, text="Произвожу запрос к сайту... Немножко подождите\n\n"
                                                    "Кстати, а вы знали что в одном яблоке всего 80 ккал?"
                                                    " Кушайте фрукты! 🍏",
                              message_id=msg_id)

        recipies = rm.parse_web(user["ingredients"])

        if len(recipies) == 0:
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(text="Понятно", callback_data=f"final"))
            bot.edit_message_text(chat_id=chat_id, text="К сожалению, рецептов с этими ингредиентами не нашлось :(\n\n"
                                                        "Попробуйте еще раз",
                                  reply_markup=kb, message_id=msg_id)
        else:
            db.set_stage(chat_id, Stages.CHECKING_RECIPIES.value)
            db.set_recipies(chat_id, recipies)
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(types.InlineKeyboardButton(text="➡️", callback_data=f"recipy_1_2"))
            kb.add(types.InlineKeyboardButton(text="Вернуться в меню", callback_data=f"final"))
            bot.delete_message(chat_id=chat_id, message_id=msg_id)

            bot.send_photo(chat_id=chat_id, caption=create_recipy_text(recipies[0]),
                           reply_markup=kb, photo=recipies[0]["link"], parse_mode='HTML')

    elif call.data.startswith("recipy"):
        _, ind, page_ind = call.data.split("_")
        ind = int(ind)
        page_ind = int(page_ind)

        recipies = db.get_recipies(chat_id)
        user = db.get_user(chat_id)
        if ind >= len(recipies):
            recipies = rm.parse_web(user["ingredients"], page_ind + 1)

            if len(recipies) == 0:
                kb = types.InlineKeyboardMarkup(row_width=1)
                kb.add(types.InlineKeyboardButton(text="Понятно", callback_data=f"final"))
                bot.edit_message_text(chat_id=chat_id,
                                      text="К сожалению, рецептов с этими ингредиентами больше не нашлось :(\n\n"
                                           "Попробуйте еще раз",
                                      reply_markup=kb, message_id=msg_id)
            else:
                db.set_stage(chat_id, Stages.CHECKING_RECIPIES.value)
                db.set_recipies(chat_id, recipies)
                kb = types.InlineKeyboardMarkup(row_width=1)
                kb.add(types.InlineKeyboardButton(text="➡️", callback_data=f"recipy_1_{page_ind + 1}"))
                kb.add(types.InlineKeyboardButton(text="Вернуться в меню", callback_data=f"final"))
                bot.delete_message(chat_id=chat_id, message_id=msg_id)

                bot.send_photo(chat_id=chat_id, caption=create_recipy_text(recipies[0]),
                               reply_markup=kb, photo=recipies[0]["link"], parse_mode='HTML')

        else:
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.row(types.InlineKeyboardButton(text="⬅️", callback_data=f"recipy_{ind - 1}_{page_ind}"),
                   types.InlineKeyboardButton(text="➡️", callback_data=f"recipy_{ind + 1}_{page_ind}"))
            kb.add(types.InlineKeyboardButton(text="Вернуться в меню", callback_data=f"final"))
            bot.delete_message(chat_id=chat_id, message_id=msg_id)

            bot.send_photo(chat_id=chat_id, caption=create_recipy_text(recipies[ind]),
                           reply_markup=kb, photo=recipies[ind]["link"], parse_mode='HTML')


if __name__ == '__main__':
    bot.polling()
