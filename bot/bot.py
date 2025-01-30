import logging
import os
import json
from io import BytesIO

import configparser
import base64

import requests
from telegram import PhotoSize, Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from yandex_api import get_answer_from_yandex
from image_processing import recognize_text_from_image

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                      text="Я помогу подготовить ответ на экзаменационный вопрос по дисциплине 'Операционные системы'.\nПришлите мне фотографию с вопросом или наберите его текстом.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                      text="Я помогу подготовить ответ на экзаменационный вопрос по дисциплине 'Операционные системы'.\nПришлите мне фотографию с вопросом или наберите его текстом.")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
        question = update.message.text
        try:
            answer = await get_answer_from_yandex(question)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)
        except Exception as e:
          logging.error(f"Error processing question: {e}")
          await context.bot.send_message(chat_id=update.effective_chat.id, text="Я не смог подготовить ответ на экзаменационный вопрос.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        # logging.info(f"Received photo list: {update.message.photo}")
        
        if update.message.media_group_id:
           await context.bot.send_message(chat_id=update.effective_chat.id, text="Я могу обработать только одну фотографию.")
           return

        photo: PhotoSize = update.message.photo[-1]
        file_id = photo.file_id
        file = await context.bot.get_file(file_id)
        file_path = file.file_path

        try:
            photo = update.message.photo[-1]
            # image_bytes = BytesIO()
            file = await photo.get_file()
            image_bytes = file.download_as_bytearray()

            # Создаем BytesIO из загруженных байтов
            # image_bytes = BytesIO(image_bytes_array)
            # Загружаем файл в BytesIO
            # await file.download_as_bytearray(image_bytes)
            # await photo.download(destination=image_bytes)
            # image_bytes.seek(0)
            photo = base64.b64encode(image_bytes.read()).decode('utf-8')
            recognized_text = await recognize_text_from_image(photo)
            
            if recognized_text:
              try:
                  answer = await get_answer_from_yandex(recognized_text)
                  await context.bot.send_message(chat_id=update.effective_chat.id, text=answer)
              except Exception as e:
                  logging.error(f"Error processing recognized text: {e}")
                  await context.bot.send_message(chat_id=update.effective_chat.id, text="Я не смог подготовить ответ на экзаменационный вопрос.")
            else:
               await context.bot.send_message(chat_id=update.effective_chat.id, text="Я не могу обработать эту фотографию.")
        except Exception as e:
            logging.error(f"Error handling photo: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Я не могу обработать эту фотографию.")

async def handle_other_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
         await context.bot.send_message(chat_id=update.effective_chat.id, text="Я могу обработать только текстовое сообщение или фотографию.")

def read_tfvars(filename="terraform.tfvars"):
    """Reads variables from a Terraform tfvars file."""
    config = configparser.ConfigParser()
    full_path = os.path.join("terraform", filename)
    try:
        with open(full_path, "r") as f:
            config.read_string("[DEFAULT]\n" + f.read())  # tfvars не имеет секций, поэтому добавляем фиктивную
        return dict(config["DEFAULT"])
    except FileNotFoundError:
        print(f"Error: File not found: {full_path}")
        exit()
    except Exception as e:
        print(f"Error reading {full_path}: {e}")
        exit()
        
if __name__ == '__main__':
        config = read_tfvars()  # Считываем переменные из файла
    
        if config: # Check if config is not None
            BOT_TOKEN = config.get('tg_bot_key')
            BOT_TOKEN = BOT_TOKEN.strip('"')
            print(f"BOT_TOKEN: {BOT_TOKEN}") 
        else:
            print("Error: Config is empty, could not retrieve the token")
            exit()

        if not BOT_TOKEN:
          print("Error: BOT_TOKEN environment variable not set.")
          exit()

        application = ApplicationBuilder().token(BOT_TOKEN).build()

        start_handler = CommandHandler('start', start)
        help_handler = CommandHandler('help', help_command)
        text_message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text_message)
        photo_handler = MessageHandler(filters.PHOTO, handle_photo)
        other_message_handler = MessageHandler(filters.ALL, handle_other_message)

        application.add_handler(start_handler)
        application.add_handler(help_handler)
        application.add_handler(text_message_handler)
        application.add_handler(photo_handler)
        application.add_handler(other_message_handler)
        # print(f"WEBHOOK_URL: {os.environ.get('WEBHOOK_URL')}")
   

        application.run_polling()

        # application.run_webhook(
        #     listen="0.0.0.0",
        #     port=int(os.environ.get("PORT", 3000)),
        #     webhook_url=os.environ.get("WEBHOOK_URL"),
        # )
