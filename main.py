# pip install pyTelegramBotAPI
import telebot
from telebot import types, telebot, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

import random

# дополнительный модуль для запросов к базе
import bd


class Command:
    ADD_WORD = "Добавить слово ➕"
    DELETE_WORD = "Удалить слово🔙"
    NEXT = "Дальше ⏭"
    CANCEL = "❌ Отмена"
    RESET = "Восстановить базовые слова"
    REPEAT = "Повторить"


class Buttons:
    NEXT = types.KeyboardButton(Command.NEXT)
    ADD = types.KeyboardButton(Command.ADD_WORD)
    DEL = types.KeyboardButton(Command.DELETE_WORD)
    CANCEL = types.KeyboardButton(Command.CANCEL)
    RESET = types.KeyboardButton(Command.RESET)
    REPEAT = types.KeyboardButton(Command.REPEAT)


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()
    new_ru_word = State()
    wait_en_word = State()
    last_words = State()
    no_words = State()
    repeat = State()


def chat_menu(cid):
    c1 = types.BotCommand(command="start", description="Запуск / перезапуск чата")
    c2 = types.BotCommand(command="help", description="Помощь")
    c3 = types.BotCommand(command="cards", description="Режим обучения")
    bot.set_my_commands([c1, c2, c3])
    bot.set_chat_menu_button(cid, types.MenuButtonCommands("commands"))


TOKEN = "8364704791:AAGhZMvus1eWqJ6UbCi64qgHpqx2ttqTsD4"
bot = telebot.TeleBot(TOKEN, state_storage=StateMemoryStorage())


@bot.message_handler(commands=["help"])
def help_command(message):
    help_text = (
        "📌 *Шпаргалка по боту*\n\n"
        "*Основные команды:*\n"
        "• /start — запустить или перезапустить бота\n"
        "• /cards — начать тренировку слов\n\n"
        "*Кнопки:*\n"
        "• ➕ Добавить слово — добавить новое слово (русское + перевод)\n"
        "• 🔙 Удалить слово — удалить текущее слово из словаря\n"
        "• ♻️ Восстановить — вернуть базовый набор слов\n"
        "• ⏭ Дальше — пропустить слово\n"
        "• 🔁 Повторить — начать тренировку заново\n\n"
        "*Как проходит тренировка:*\n"
        "1. Бот показывает русское слово 🇷🇺\n"
        "2. Ты выбираешь правильный перевод 🇬🇧 из кнопок\n"
        "3. Бот считает правильные ✅, ошибки ❌ и пропуски ⏭\n\n"
        "💡 Совет: проходи карточки каждый день, чтобы слова закрепились!"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")


def count(message, cnt):
    bot.send_message(
        message.from_user.id,
        f"В вашем словаре сейчас {cnt[3]} слов.\nИз них "
        f"{cnt[1]- cnt[2]} базовых.\n(Базовых удалено: {cnt[2]})",
    )
    if cnt[3] <= 0:
        markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
        buttons = []
        buttons.extend([Buttons.RESET, Buttons.ADD])
        markup.add(*buttons)
        bot.send_message(
            message.from_user.id,
            f"Нужно что-нибудь добавить или восстановить базовый набор слов, чтобы можно было начать.",
            reply_markup=markup,
        )
        bot.set_state(message.from_user.id, MyStates.no_words, message.chat.id)


# Перезапуск урока
@bot.message_handler(state=MyStates.repeat)
def no_words(message):
    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        data["passed_words"] = set()
        data["skip"] = 0
        data["correct"] = 0
        data["wrong"] = 0
    start_bot(message)


@bot.message_handler(commands=["start"])
def init(message):
    welcome_text = (
        "👋 Приветствую! Давай позанимаемся английским!\n\n"
        "📌 Что умеет бот:\n"
        "• Тренировка слов в формате карточек\n"
        "• Добавление и удаление слов\n"
        "• Восстановление базового словаря\n"
        "• Подсчёт прогресса и повторение\n\n"
        "⚡ Быстрые команды:\n"
        "• /cards — начать тренировку\n"
        "• /help — полная шпаргалка\n\n"
        "💡 Совет: начни с команды /cards, а потом добавляй свои слова!"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    cnt = bd.count(message.from_user.id)
    count(message, cnt)
    if cnt[3] > 0:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["passed_words"] = set()
            data["skip"] = 0
            data["correct"] = 0
            data["wrong"] = 0
        start_bot(message)


# Обработчик кнопки восстановления базовых слов
@bot.message_handler(func=lambda message: message.text == Command.RESET)
def reset(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return
    bd.reset(message.from_user.id)
    cnt = bd.count(message.from_user.id)
    bot.send_message(
        message.from_user.id,
        f"Базовый набор слов восстановлен!",
    )
    count(message, cnt)
    start_bot(message)


# реакция на кнопку выхода из режима добавления слова
@bot.message_handler(func=lambda message: message.text == Command.CANCEL)
def next_cards(message):
    start_bot(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    cid = message.chat.id
    cnt = bd.count(message.from_user.id)
    count(message, cnt)
    if cnt[2] > 0:
        bot.send_message(
            cid,
            "ВЫ можете восстановить удаленные слова из базового набора слов, или добавить новое слово.",
            reply_markup=markup,
        )
    buttons = [Buttons.CANCEL]
    if cnt[2] > 0:
        buttons.append(Buttons.RESET)
    markup.add(*buttons)
    bot.set_state(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        state=MyStates.new_ru_word,
    )
    bot.send_message(cid, "Отправьте русское слово", reply_markup=markup)


@bot.message_handler(state=MyStates.new_ru_word)
def got_ru(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return

    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = []

    text: str = message.text

    text = text.lower()
    alphabet = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
    alph_ext = alphabet.union(" -")
    answer = f'Вы отправили: "{text}"\n\n'

    if (
        alphabet.isdisjoint(text.lower()[0])
        or alphabet.isdisjoint(text.lower()[-1])
        or alph_ext.isdisjoint(text.lower())
        or len(text) > 20
    ):
        answer += """Русское слово может содержать только:\n
        русские символы, дефис, пробел.
        Должно начинаться с русской буквы.
        Должно заканчиваться русской буквой.
        Не должно быть длинее двадцати символов.\n\nПожалуйста, отправьте корректное слово."""
    else:
        result, tr = bd.add_word(message.from_user.id, text, None)
        if result == 1:
            answer += (
                "Это слово присутствует в базовом наборе слов и доступно в вашем словаре, "
                "оно загадывается вам во время тренеровок.\nЕго нельзя добавть снова."
            )
            bot.send_message(message.chat.id, answer)
            start_bot(message)
            return
        if result == 2:
            answer += (
                "Это слово присутствует в базовом наборе слов и было"
                " удалено вами.\n"
                "Сейчас оно восстановлено и доступно в вашем словаре, и будет загадывается вам "
                "во время тренеровок."
            )
            bot.send_message(message.chat.id, answer)
            start_bot(message)
            return
        if result == 3:
            bot.send_message(
                message.chat.id,
                answer + "Произошла техническая ошибка. Повторите попытку позже.",
            )
            start_bot(message)
            return
        if result == 4:
            answer += (
                "Это слово уже присутствует в в вашем словаре с переводом:"
                f" '{tr}'\n\n"
                "Если вы продолжите, перевод будет изменен на новый.\n\n"
            )
        # Временно сохраняем слово
        with bot.retrieve_data(
            user_id=message.from_user.id, chat_id=message.chat.id
        ) as data:
            data["new_word"] = text
        answer += "Отправьте перевод слова на английский:"
        # buttons.append(types.KeyboardButton(message.text))
        # handler = got_en
        bot.set_state(
            user_id=message.from_user.id,
            chat_id=message.chat.id,
            state=MyStates.wait_en_word,
        )

    buttons.append(types.KeyboardButton(Command.CANCEL))
    markup.add(*buttons)

    msg = bot.send_message(message.chat.id, answer, reply_markup=markup)


@bot.message_handler(state=MyStates.wait_en_word)
def got_en(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return

    text: str = message.text

    text = text.lower()
    alphabet = set("abcdefghijklmnopqrstuvwxyz")
    alph_ext = alphabet.union(" -")

    # Временно сохраняем слово
    with bot.retrieve_data(
        user_id=message.from_user.id, chat_id=message.chat.id
    ) as data:
        ru = data["new_word"]

    answer = f'Вы отправили русское слово: "{ru}"\n'
    answer += f'Вы отправили английское слово: "{text}"\n\n'
    if (
        alphabet.isdisjoint(text.lower()[0])
        or alphabet.isdisjoint(text.lower()[-1])
        or alph_ext.isdisjoint(text.lower())
        or len(text) > 20
    ):
        answer += """Английское слово может содержать только:\n
        латинские символы, дефис, пробел.
        Должно начинаться с латинской буквы.
        Должно заканчиваться латинской буквой.
        Не должно быть длинее двадцати символов.\n\nПожалуйста, отправьте корректное слово."""
    else:
        result = bd.add_word(message.from_user.id, ru, text)[0]
        if result == 0:
            answer += "Слово успешно добавлено!"
    bot.send_message(message.chat.id, answer)
    count(message, bd.count(message.from_user.id))
    start_bot(message)


def repeat(message):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    buttons = [Buttons.REPEAT]
    markup.add(*buttons)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        bot.send_message(
            message.chat.id,
            "Поздравляем, вы завершили все задания\n\n"
            + "Ваш результат:\n"
            + f"    Правильных ответов: {data["correct"]}\n"
            + f"    Пропушено: {data['skip']}\n"
            + f"    Ошибок: {data["wrong"]}\n",
            reply_markup=markup,
        )
    bot.set_state(message.from_user.id, MyStates.repeat, message.chat.id)


@bot.message_handler(commands=["cards"])
def start_bot(message):
    chat_menu(message.chat.id)
    if not bot.get_state(message.from_user.id):
        init(message)
        return

    cnt = bd.count(message.from_user.id)
    if cnt[3] <= 0:
        count(message, cnt)
        return

    markup = types.ReplyKeyboardMarkup(row_width=2)
    words, others = bd.get_words(message.from_user.id)

    # ru_word = "Мир"  # брать из БД
    # en_word = "Peace"  # брать из БД
    # others = ["Green", "White", "Hello"]  # брать из БД

    i = 0
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        while True:
            i = random.randint(0, len(words) - 1)
            if words[i][0] in data["passed_words"]:
                words.pop(i)
                continue
            break
        word = words[i]
        ru_word = word[0]
        en_word = word[1]
        others.remove(en_word)
        others = list(others)
        random.shuffle(others)
        others = others[0:3]
    buttons = []

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if len(data["passed_words"]) >= cnt[3]:
            repeat(message)
            return
        bot.send_message(
            message.chat.id,
            f"Прогресс: [{len(data['passed_words'])}/{cnt[3]}]",
        )

    target_word_btn = types.KeyboardButton(en_word)
    buttons.append(target_word_btn)

    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {ru_word}"

    buttons.extend([Buttons.NEXT, Buttons.ADD, Buttons.DEL])

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["buttons"] = buttons

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        greeting,
        reply_markup=markup,
    )

    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["target_word"] = en_word
        data["translate_word"] = ru_word
        data["other_words"] = others


# пропуск слова
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["passed_words"].add(data["translate_word"])
        data["skip"] += 1

    start_bot(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        word = data["translate_word"]
    bd.del_word(message.from_user.id, word)
    bot.send_message(message.chat.id, 'Удалено успешно"')
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["passed_words"].remove(data["translate_word"])
    cnt = bd.count(message.from_user.id)
    count(message, cnt)
    if cnt[3] == 0:
        return
    start_bot(message)


# все остальные ситуации
@bot.message_handler(func=lambda message: True, content_types=["text"])
def message_reply(message):
    if not bot.get_state(message.from_user.id):
        start_bot(message)
        return

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data: dict
        if "target_word" in data.keys():
            target_word = data["target_word"]
        else:
            start_bot(message)
            return

    if message.text == target_word:
        answer = "Отлично!❤\n\n"
        answer += f"{data['target_word']} -> {data['translate_word']}"
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["passed_words"].add(data["translate_word"])
            data["correct"] += 1

        bot.send_message(message.chat.id, answer)
        start_bot(message)
    else:
        markup = types.ReplyKeyboardMarkup(row_width=2)
        buttons = []
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data["wrong"] += 1
            buttons = data["buttons"]

        for btn in buttons:
            if btn.text == message.text:
                btn.text = message.text + "❌"
                break

        markup.add(*buttons)
        text = (
            "Допущена ошибка!\n"
            f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}"
        )

        bot.send_message(message.chat.id, text, reply_markup=markup)


if __name__ == "__main__":
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    print("Bot is running!")
    bot.infinity_polling(skip_pending=True)
