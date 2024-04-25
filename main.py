import telebot
import json
import requests
import os
from datetime import datetime

bot = telebot.TeleBot("MEOW")

@bot.message_handler(commands=['start'])
def start(message):
    photo_url = "https://images.wallpapersden.com/image/download/new-nier-automata-art_a21taWyUmZqaraWkpJRmbmdlrWZlbWU.jpg"
    bot.send_photo(message.chat.id, photo_url)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("JSON TO NETSCAPE", "NETSCAPE TO JSON")
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

    inline_button = telebot.types.InlineKeyboardButton("АВТОР", url="https://zelenka.guru/qiyanaitsme/")
    inline_markup = telebot.types.InlineKeyboardMarkup().add(inline_button)
    bot.send_message(message.chat.id, "Нажмите на кнопку для перехода к автору:", reply_markup=inline_markup)

@bot.message_handler(func=lambda message: message.text == 'JSON TO NETSCAPE')
def json_to_netscape(message):
    bot.send_message(message.chat.id, "Отправьте файл JSON:")
    bot.register_next_step_handler(message, process_file_json_to_netscape)

def process_file_json_to_netscape(message):
    try:
        file_content = message.document
        if file_content.file_name.endswith('.json'):
            file_info = bot.get_file(file_content.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            json_data = json.loads(downloaded_file.decode('utf-8'))
            netscape_data = json.dumps(json_data, separators=(',', ':'))
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            folder_path = f"conversion_{current_date}"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            
            with open(f"{folder_path}/netscape_data.txt", 'w') as file:
                file.write(netscape_data)
            
            with open(f"{folder_path}/netscape_data.txt", 'rb') as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.send_message(message.chat.id, "Формат файла должен быть .json.")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обработке файла: " + str(e))

@bot.message_handler(func=lambda message: message.text == 'NETSCAPE TO JSON')
def netscape_to_json(message):
    bot.send_message(message.chat.id, "Отправьте файл в формате NETSCAPE:")
    bot.register_next_step_handler(message, process_file_netscape_to_json)

def process_file_netscape_to_json(message):
    try:
        file_content = message.document
        if file_content.file_name.endswith('.txt'):
            file_info = bot.get_file(file_content.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            netscape_data = downloaded_file.decode('utf-8')
            json_data = json.loads(netscape_data)
            
            current_date = datetime.now().strftime("%Y-%m-%d")
            folder_path = f"conversion_{current_date}"
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            with open(f"{folder_path}/json_data.json", 'w') as file:
                json.dump(json_data, file, indent=2)
            
            with open(f"{folder_path}/json_data.json", 'rb') as file:
                bot.send_document(message.chat.id, file)
        else:
            bot.send_message(message.chat.id, "Формат файла должен быть .txt.")
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обработке файла: " + str(e))

bot.polling()
