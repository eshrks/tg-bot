import os
from random import choice
from keep_alive import keep_alive
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types


GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')
conversation = model.start_chat(history=[])

bot = Bot(os.environ.get("BOT_TOKEN"))
dp = Dispatcher(bot)
chat_id = int(os.environ.get("PRIVATE"))


async def send_long_message(chat_id, text):
    chunk_size = 4096
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    for chunk in chunks:
        await bot.send_message(chat_id=chat_id, text=chunk)


@dp.message_handler(commands=['start'])
async def start(message):
  user_name = message.from_user.first_name
  await bot.send_message(chat_id=chat_id, text=f"Wassup {user_name}, Nice to meet you!")


@dp.message_handler(commands=['clear'])
async def clear(message):
    if message.chat.id == chat_id:
        conversation.history = []
        await bot.send_message(chat_id=chat_id, text="Conversation has been reset.")


@dp.message_handler(commands=['info'])
async def info(message):
    if message.chat.id == chat_id:
        random_info = [
            "I'm glad you're interested about me :)",
            "I am powered by Gemini Pro.",
            "Ask me anything, I will try my best to help.",
            "I'm just fine, how about you?"
        ]
        await message.reply(choice(random_info))


@dp.message_handler(commands=['help'])
async def helper(message):
    user_name = message.from_user.first_name
    if message.chat.id == chat_id:
        help_command = f"""
Hello there {user_name}👋, this is the command list that you may use:
/help - use this help menu
/info - display about information
/clear - clear the past conversation

Feel free to ask any questions. 😊
        """
        await message.answer(help_command)


@dp.message_handler(content_types=types.ContentType.TEXT)
async def brain(message: types.Message):
    if message.chat.id == chat_id:
            stream = True if conversation.history else False
            response = conversation.send_message(message.text, stream=stream)
            for i in response:
                ...
            await send_long_message(chat_id=chat_id, text=response.text)


if __name__ == '__main__':
    from aiogram import executor

    keep_alive()
    executor.start_polling(dp, skip_updates=True)
