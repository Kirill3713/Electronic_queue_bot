# Импортируем модули
import telebot
from config import api_token
import logging
import json
from datetime import date, timedelta, datetime
from telebot import types
# Объявляем переменные
TOKEN = api_token
bot = telebot.TeleBot(TOKEN)
# Создаем функции
def add_appointment(date, time, client):
    """
    Добавление записи.
    """
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}
    data["appointments"].append(
        {
            "date": date,
            "time": time,
            "client": client
        }
    )
    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False)
def clean_appointments():
    """
    Очистка старых записей.
    """
    # Загрузка данных
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        return
    # Проверка даты
    for appointment in data["appointments"]:
        appointment_date = list(map(int, appointment["date"].split(".")))
        today = list(map(int, str(datetime.today().date()).split("-")))
        if appointment_date[2] < today[0]:
            data["appointments"].remove(appointment)
        elif appointment_date[2] == today[0] and appointment_date[1] < today[1]:
            data["appointments"].remove(appointment)
        elif appointment_date[2] == today[0] and appointment_date[1] == today[1] and appointment_date[0] < today[2]:
            data["appointments"].remove(appointment)
        elif appointment_date[2] == today[0] and appointment_date[1] == today[1] and appointment_date[0] == today[2]:
            # Проверка времени
            if int(appointment["time"][:2]) < int(datetime.now().time().hour):
                data["appointments"].remove(appointment)
            elif int(appointment["time"][:2]) == int(datetime.now().time().hour) and int(appointment["time"][3:]) < int(datetime.now().time().minute):
                data["appointments"].remove(appointment)
    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False) 
def generate_keyboard(button_names, prefix):
    """
    Создание кнопок.
    """
    keyboard = types.InlineKeyboardMarkup()

    for name in button_names:
        data = f"{prefix}: {name}"
        button = types.InlineKeyboardButton(f"{name}", callback_data=f"{data}") # callback_data всегда строка
        keyboard.add(button)

    return keyboard
def generate_time_keyboard(button_names, prefix, date):
    """
    Создание кнопок с временем.
    """
    keyboard = types.InlineKeyboardMarkup()

    for name in button_names:
        data = f"{prefix}, {date}, {name}"
        button = types.InlineKeyboardButton(f"{name}", callback_data=f"{data}") # callback_data всегда строка
        keyboard.add(button)

    return keyboard
def add_review(message):
    """
    Добавление отзыва.
    """
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}
    data["review"].append(
        {
            "client": str(message.chat.id),
            "text": message.text
        }
    )
    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False)
    bot.send_message(message.chat.id, "Ваш отзыв успешно добавлен!")

def add_name(message):
    """
    Добавление имени.
    """
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}
    data["clients"][str(message.chat.id)] = message.text

    with open("data.json", "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, ensure_ascii=False)
    bot.send_message(message.chat.id, f"Ваше имя изменено на {message.text}.")
# Декоратор
@bot.message_handler(commands=["start"])
def handle_start(message):
    logging.info("Начинаем работу бота")
    bot.send_message(message.chat.id, "Добрый день. Этот бот поможет Вам записаться на консультацию.")

@bot.message_handler(commands=["show_dates"])
def handle_show_dates(message):
    logging.info("Запись")
    # Выбор даты
    keyboard = generate_keyboard([date.strftime(date.today()+timedelta(x+3), "%d.%m.%Y") for x in range(7)], "дата")
    bot.send_message(message.chat.id, "Выберите дату:", reply_markup=keyboard)

@bot.message_handler(commands=["show_appointments"])
def handle_show_appointments(message):
    logging.info("Просмотр всех записей")
    clean_appointments()
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}
    empty = True
    if data != {}:
        for appointment in data["appointments"]:
            if appointment["client"] == str(message.chat.id):
                empty = False
    if not empty:
        n = 1
        bot.send_message(message.chat.id, "Ваши записи:\n________________")
        for appointment in data["appointments"]:
            if appointment["client"] == str(message.chat.id):
                bot.send_message(message.chat.id, f"Запись №{n}:\nДата: {appointment["date"]}\nВремя: {appointment["time"]}\n________________")
                n += 1
    else:
        bot.send_message(message.chat.id, "Вы пока не записаны на прием. Чтобы забронировать время используйте функцию /show_dates")

@bot.message_handler(commands=["add_review"])
def handle_add_review(message):
    logging.info("Добавление отзыва")
    bot.send_message(message.chat.id, "Напишите свой отзыв, пожалуйста.")
    bot.register_next_step_handler_by_chat_id(message.chat.id, add_review)


@bot.message_handler(commands=["set_name"])
def handle_set_name(message):
    logging.info("Изменение имени")
    try:
        with open("data.json", "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except FileNotFoundError:
        data = {}
    if data != {}:
        if message.chat.id in list(data["clients"].keys()):
            name = data["clients"][str(message.chat.id)]
        else:
            name = message.chat.first_name
    else:
        name = message.chat.first_name

    keyboard = generate_keyboard(["Да", "Нет"], "y/n keyboard")
    bot.send_message(message.chat.id, f"Вы записаны под имением {name}. Вы желаете изменить имя?", reply_markup=keyboard)
@bot.message_handler(commands=["help"])
def handle_help(message):
    logging.info("Справка")
    bot.send_message(message.chat.id, "Приветствуем Вас в нашем боте! С его помощью Вы можете записаться в нашу электронную очередь. Наш бот имеет небольшой список команд. Предлагаем Вам ознакомиться с ним:\n\n/start - Эта команда запускает бота и позволяет Вам начать работу с ним.\n/show_dates - Эта команда позволяет Вам сделать запись. Она предлагает Вам свободные даты и время.\n/show_appointments - После выбора этой команды Вам будут показаны все Ваши записи.\n/add_review - Здесь Вы можете оставить свой отзыв.\n/set_name - Эта команда поможет изменить имя, которым мы будем к Вам обращаться.\n/help - Это команда справки, она расскажет Вам о работе нашего бота.\n\nЧтобы запустить любую команду необходимо либо выбрать ее в меню команд бота, либо нажать на ее название из этого сообщения, либо написать ее используя символ / перед названием.\n\nПриятной работы!")
@bot.callback_query_handler(lambda call:True)
def handle_button_click(call):
    if "дата" in call.data:
        date = call.data.replace("дата: ", "")
        bot.send_message(call.message.chat.id, f"Вы выбрали дату '{date}'")
        # Клавиатура с доступным временем
        time_list = ["10:00", "11:00", "12:00", "15:00","16:00", "17:00"]
        try:
            with open("data.json", "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
        except FileNotFoundError:
            data = {}
        if data != {}:
            for appointment in data["appointments"]:
                if appointment["time"] in time_list and appointment["date"] == date:
                    time_list.remove(appointment["time"])
        if time_list != []:
            keyboard = generate_time_keyboard(time_list, "время", date)
            bot.send_message(call.message.chat.id, "Выберите время:", reply_markup=keyboard)
        else:
            bot.send_message(call.message.chat.id, "Извините, на этот день нет свободного времени.")

    if "время" in call.data:
        data = call.data.replace("время, ", "").split(", ")
        bot.send_message(call.message.chat.id, f"Вы записаны на {data[1]}.")

        add_appointment(data[0], data[1], str(call.message.chat.id))
    if "y/n" in call.data:
        data = call.data.replace("y/n keyboard: ", "")
        if data == "Да":
            bot.send_message(call.message.chat.id, "Введите новое имя:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, add_name)
        else:
            bot.send_message(call.message.chat.id, "Мы будем обращаться к вам по-прежнему.")
# Точка входа
if __name__ == "__main__":
    bot.polling(non_stop=True)