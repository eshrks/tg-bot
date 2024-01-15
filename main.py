import os
from random import choice
from keep_alive import keep_alive
import google.generativeai as genai
from aiogram import Bot, Dispatcher, types
from google.generativeai.types import generation_types


GOOGLE_API_KEY = os.environ.get('GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

bot = Bot(os.environ.get("BOT_TOKEN"))
dp = Dispatcher(bot)
chat_id = int(os.environ.get("PRIVATE"))

usernames = {os.environ.get("PRIV_UN"): model.start_chat(history=[])}


async def show_loading_prompt(chat_id):
    loading_message = await bot.send_message(chat_id=chat_id, text="Processing... ⏳")
    return loading_message.message_id


async def send_long_message(user_input, response, loading_message):
    chunk_size = 4096
    chunks = [response[i:i + chunk_size] for i in range(0, len(response), chunk_size)]
    for chunk in chunks:
        await bot.edit_message_text(chat_id=user_input.chat.id, message_id=loading_message, text=chunk)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    first_name = message.from_user.first_name
    await message.answer(f"Wassup {first_name}, Nice to meet you!")

    fullname = message.from_user.full_name
    username = message.from_user.username
    user_id = message.chat.id
    permission = f"""
{fullname} is asking for permission to use me 🥹

username: "{username}"
user_id: {user_id}
"""
    await bot.send_message(chat_id=chat_id, text=permission)


@dp.message_handler(commands=['clear'])
async def clear(message: types.Message):
    if usernames.get(message.from_user.username):
        person = usernames[message.from_user.username]
        person.history = []
        await message.answer("Conversation has been reset.")


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    if usernames.get(message.from_user.username):
        random_info = [
            "I'm glad you're interested about me :)",
            "I am powered by Gemini Pro.",
            "Ask me anything, I will try my best to help.",
            "I'm just fine, how about you?"
        ]
        await message.reply(choice(random_info))


@dp.message_handler(commands=['help'])
async def helper(message: types.Message):
    if usernames.get(message.from_user.username):
        first_name = message.from_user.first_name
        commando = """
/start - starter command
/help - use this help menu
/info - display about information
/clear - clear the past conversation
/grant - add username w/o @
/revoke - remove username
/view - view granted usernames
"""
        help_command = f"""
Hello there {first_name}👋, this is the command list that you may use:
/help - use this help menu
/info - display about information
/clear - clear the past conversation

Feel free to ask any questions. 😊
"""
        txt = commando if message.chat.id == chat_id else help_command
        await message.answer(txt)


@dp.message_handler(commands=['grant'])
async def valid(message: types.Message):
    if message.chat.id == chat_id:
        username = message.get_args()
        if username == "":
            await bot.send_message(chat_id=chat_id, text="/grant expect a username.")
        elif username in usernames.keys():
            await bot.send_message(chat_id=chat_id, text=f"{username} is already in the list.")
        else:
            usernames[username] = model.start_chat(history=[])
            await bot.send_message(chat_id=chat_id, text=f"{username} has been added to the list.")


@dp.message_handler(commands=['revoke'])
async def revoke(message: types.Message):
    if message.chat.id == chat_id:
        username = message.get_args()
        if username == "":
            await bot.send_message(chat_id=chat_id, text="/revoke expect a username.")
        elif username not in usernames.keys():
            await bot.send_message(chat_id=chat_id, text=f"{username} not found.")
        else:
            usernames.pop(username)
            await bot.send_message(chat_id=chat_id, text=f"{username} removed.")


@dp.message_handler(commands=['view'])
async def view(message: types.Message):
    if message.chat.id == chat_id:
        description = "Here's the list of Granted Users:\n"
        un = "\n".join([f"{num}. {key}" for num, key in enumerate(usernames.keys(), start=1)])
        await bot.send_message(chat_id=chat_id, text=f'{description}{un}')


@dp.message_handler(content_types=types.ContentType.TEXT)
async def brain(message: types.Message):
    if usernames.get(message.from_user.username):
        try:
            loading_message = await show_loading_prompt(message.chat.id)
            person = usernames[message.from_user.username]

            stream = True if person.history else False
            response = person.send_message(message.text, stream=stream)
            for i in response:
                ...
            await send_long_message(message, response.text, loading_message)
        except generation_types.BlockedPromptException:
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=loading_message,
                                        text="Response blocked due to safety concerns.")


if __name__ == '__main__':
    from aiogram import executor

    keep_alive()
    executor.start_polling(dp, skip_updates=True)
