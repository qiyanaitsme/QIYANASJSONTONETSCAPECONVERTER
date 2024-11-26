import telebot
import json
import threading
import io
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

bot = telebot.TeleBot("MEOW")

class FileProcessor:
    def __init__(self):
        self.stats = []
        self.files_buffer = {}
        self.timers = {}
        self.conversion_type = {}
        self.TIMEOUT = 5

    def add_file(self, chat_id, file_data, conv_type):
        if chat_id not in self.files_buffer:
            self.files_buffer[chat_id] = []
            self.conversion_type[chat_id] = conv_type
        
        if self.conversion_type[chat_id] != conv_type:
            return False
            
        self.files_buffer[chat_id].append(file_data)
        
        if chat_id in self.timers and self.timers[chat_id]:
            self.timers[chat_id].cancel()
        
        timer = threading.Timer(self.TIMEOUT, self.process_batch, args=[chat_id])
        self.timers[chat_id] = timer
        timer.start()
        return True

    def create_zip_archive(self, files_data):
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for filename, content in files_data:
                zf.writestr(filename, content)
        memory_zip.seek(0)
        return memory_zip

    def process_batch(self, chat_id):
        if not self.files_buffer.get(chat_id):
            return

        files = self.files_buffer[chat_id]
        conv_type = self.conversion_type[chat_id]
        self.files_buffer[chat_id] = []
        
        bot.send_message(chat_id, f"🔄 Начинаю конвертацию {len(files)} файлов...")

        converted_files = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self.convert_file, file_data, conv_type)
                for file_data in files
            ]
            
            for future in futures:
                try:
                    result = future.result()
                    if result:
                        input_filename, output_data = result
                        ext = '.txt' if conv_type == 'json_to_netscape' else '.json'
                        output_filename = input_filename.rsplit('.', 1)[0] + ext
                        converted_files.append((output_filename, output_data))
                        self.stats.append((input_filename, output_filename))
                except Exception as e:
                    bot.send_message(chat_id, f"❌ Ошибка конвертации: {str(e)}")

        if converted_files:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"converted_files_{timestamp}.zip"
            zip_file = self.create_zip_archive(converted_files)
            zip_file.name = archive_name
            
            bot.send_document(chat_id, zip_file)

        stats_message = "✅ Конвертация завершена!\n\n📊 Итоги:\n"
        stats_message += f"📥 Всего файлов: {len(files)}\n"
        stats_message += f"📤 Успешно конвертировано: {len(converted_files)}\n"
        bot.send_message(chat_id, stats_message)

    def convert_file(self, file_data, conversion_type):
        filename, content = file_data
        try:
            if conversion_type == 'json_to_netscape':
                json_data = json.loads(content.decode('utf-8'))
                return filename, json.dumps(json_data, separators=(',', ':'))
            else:
                json_data = json.loads(content.decode('utf-8'))
                return filename, json.dumps(json_data, indent=2)
        except Exception:
            return None

processor = FileProcessor()

@bot.message_handler(commands=['start'])
def start(message):
    photo_url = "https://images.wallpapersden.com/image/download/new-nier-automata-art_a21taWyUmZqaraWkpJRmbmdlrWZlbWU.jpg"
    bot.send_photo(message.chat.id, photo_url)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("JSON В NETSCAPE", "NETSCAPE В JSON")
    markup.row("📊 СТАТИСТИКА")
    bot.send_message(message.chat.id, "Выберите тип конвертации:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["JSON В NETSCAPE", "NETSCAPE В JSON"])
def set_conversion_mode(message):
    chat_id = message.chat.id
    conv_type = 'json_to_netscape' if message.text == "JSON В NETSCAPE" else 'netscape_to_json'
    processor.conversion_type[chat_id] = conv_type
    
    file_type = "JSON" if conv_type == 'json_to_netscape' else "NETSCAPE"
    bot.send_message(chat_id, f"Отправьте файлы {file_type} для конвертации\nКонвертация начнется автоматически через {processor.TIMEOUT} секунд после последнего файла")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    chat_id = message.chat.id
    
    if chat_id not in processor.conversion_type:
        bot.send_message(chat_id, "❌ Сначала выберите тип конвертации!")
        return

    conv_type = processor.conversion_type[chat_id]
    expected_ext = '.json' if conv_type == 'json_to_netscape' else '.txt'
    
    if not message.document.file_name.endswith(expected_ext):
        bot.send_message(chat_id, f"❌ Ожидается файл с расширением {expected_ext}")
        return

    file_info = bot.get_file(message.document.file_id)
    file_content = bot.download_file(file_info.file_path)
    
    if processor.add_file(chat_id, (message.document.file_name, file_content), conv_type):
        bot.send_message(chat_id, f"📥 Файл {message.document.file_name} добавлен в очередь")
    else:
        bot.send_message(chat_id, "❌ Нельзя смешивать разные типы конвертации")

@bot.message_handler(func=lambda message: message.text == '📊 СТАТИСТИКА')
def show_statistics(message):
    if not processor.stats:
        bot.send_message(message.chat.id, "📊 Статистика конвертаций пока отсутствует")
        return
        
    stats_message = "📊 Статистика конвертаций:\n\n"
    for stat in processor.stats:
        stats_message += f"📥 Входящий файл: {stat[0]}\n📤 Исходящий файл: {stat[1]}\n➖➖➖➖➖➖\n"
    
    bot.send_message(message.chat.id, stats_message)

bot.polling()
