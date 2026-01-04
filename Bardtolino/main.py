import re
import json
import secrets
from os import getenv, remove
from string import ascii_letters

from dotenv import load_dotenv
from anthropic import Anthropic
from translate import Translator
from mysql.connector import pooling
from gemini_webapi import GeminiClient # https://github.com/HanaokaYuzu/Gemini-API
from aiogram.utils.markdown import link
from aiogram import Bot, Dispatcher, types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

import database as db


load_dotenv()
bot: str = Bot(getenv('BARDTOLINO'))
dp = Dispatcher(bot)
Secure_1PSID: str = getenv('GEMINI_API_KEY3')
Secure_1PSIDTS: str = getenv('GEMINI_API_KEY3_1')
anthropic_client: str = Anthropic(api_key=getenv('ANT_API_KEY'))
connection_pool = pooling.MySQLConnectionPool(
	pool_name=getenv('COL_8'),
	host=getenv('HORSE'),
	port=int(getenv('PURGE')),
	user=getenv('SUPERBOOK'),
	password=getenv('SUPERPOWER'),
	database=getenv('DRUM')
	)


# ~~~~~~~~~ CHECKING FOR A VALID USER ~~~~~~~~~
class CheckUserMiddleware(BaseMiddleware):
    async def on_process_message(self, message: types.Message, data: dict) -> None:
        user_id: int = message.from_user.id
        user: int = db.is_user_exist(connection_pool=connection_pool, user_id=user_id)
        if user == 0:
            raise CancelHandler()


dp.middleware.setup(CheckUserMiddleware())


# ~~~~~~~~~ (5) FUNCTIONS FOR GEMINI API ~~~~~~~~~
async def save_image_from_user(image) -> str:
	try:
		photo_id = image[-1].file_id
		file = await bot.get_file(photo_id)
		await file.download()
		return file.file_path
	except Exception as e:
		print(f"\nError in saving the image from user:\n{e}\n")


async def ask_gemini(connection_pool, user_id: int, prompt: str, image: str | None = None) -> list:
	try:
		client = GeminiClient(secure_1psid=Secure_1PSID, secure_1psidts=Secure_1PSIDTS) # v1.0.2
		await client.init(timeout=30, auto_close=True, close_delay=30, auto_refresh=False) # v1.0.2

		# temporary fix: checks every user prompt if contains a request for an image, if so then it will append a post script
		# keywords = ['image', 'photo', 'picture']
		# if any(keyword in prompt.lower() for keyword in keywords):
		# 	prompt += " P.S. Don't provide an image from web, provide a generated image instead. Thanks :)"
		# print(prompt)
		
		metadata = db.select_metadata(connection_pool=connection_pool, user_id=user_id)
		chat_session = client.start_chat(metadata=json.loads(metadata) if metadata else None) # This uses the existing string of metadata or either None
		response = await chat_session.send_message(prompt=prompt, image=image)
		updated_metadata = json.dumps(chat_session.metadata)
		db.update_metadata(connection_pool=connection_pool, user_id=user_id, metadata=updated_metadata)
		return response
	except Exception as e:
		print(f"\nError in ask_gemini function: {e}\n")


async def save_generated_image(image) -> str:
	try:
		filename: str = ''.join(secrets.choice(ascii_letters) for _ in range(6)) + ".png"
		await image.save(path="photos/", filename=filename)
		return f"photos/{filename}"
	except Exception as e:
		print(f"Unknown Error Occured in saving image:\n{e}\nThis image caused error:\n{image}")


async def send_response_image(user_id: int, response_images: list, message: types.Message) -> None:
	try:
		if response_images:
			total_images: int = len(response_images)
			title1: str = response_images[0].title
			if "Image of" in title1:
				for i, image in enumerate(response_images, start=1):
					try:
						caption: str = f"({i}/{total_images}) {image.alt}"
						await bot.send_photo(chat_id=user_id, photo=image.url, caption=caption)
					except Exception as e:
						print(f"\nUnknown Error in sending image:\n{e}\nThis image caused error\n{image}\n")
						await message.answer(f"({i}/{total_images}) failed to be sent, it's super shy")
			elif "Generated Image" in title1:
				for i, image in enumerate(response_images, start=1):
					try:
						caption: str = f"({i}/{total_images}) {image.alt}"
						photo: str = await save_generated_image(image)
						with open(photo, 'rb') as img:
							await bot.send_photo(chat_id=user_id, photo=img, caption=caption)
						remove(photo)
					except Exception as e:
						print(f"\nUnknown Error in sending image:\n{e}\nThis image caused error\n{image}\n")
						await message.answer(f"({i}/{total_images}) failed to be sent, it's super shy")
	except Exception as e:
		print(f"\nError in send_response_image function:\n{e}\n")


def fix_formatting(text) -> str:
	try:
		text = re.sub(r"\[.*?\]", '', text)
		text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
		return text
	except Exception as e:
		return "My apologies for the inconvenience, we will temporarily terminate the program to fix it. 💐"


# ~~~~~~~~~ (2) FUNCTIONS FOR TRANSLATE API ~~~~~~~~~
def translate_text(text: str, from_language: str, to_language: str) -> str:
	translator = Translator(from_lang=from_language, to_lang=to_language)
	chunk_size: int = 500
	if len(text) <= chunk_size:
		return translator.translate(text)
	else:
		chunks: list = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
		return ''.join(translator.translate(chunk) for chunk in chunks)


async def create_inline_keyboard(callback_data_name: str, rem_keeb: str | None = None):
	languages: dict = {
	'English': 'en', 'Filipino': 'tl', 
	'Japanese': 'ja', 'Korean': 'ko',
	'Spanish': 'es', 'French': 'fr'
	}
	if rem_keeb:
		languages: dict = {key: value for key, value in languages.items() if value != rem_keeb}

	buttons: list = [
	types.InlineKeyboardButton(text=key, callback_data=f"{callback_data_name}:{value}")
	for key, value in languages.items()
	]

	keyboard = types.InlineKeyboardMarkup(row_width=2)
	keyboard.add(*buttons)
	return keyboard


# ~~~~~~~~~ (1) FUNCTION FOR CLAUDE API ~~~~~~~~~
def ask_claude(prompt: str) -> str:
	try:
		message = anthropic_client.messages.create(
			model="claude-3-haiku-20240307",
			max_tokens=512,
			messages=[{"role": "user", "content": prompt}])
		return message.content[0].text
	except Exception as e:
		print(f"Error Occurred in Claude:\n{e}")
		return "My apologies for the inconvenience, we will temporarily terminate the program to fix it. 💐"


# ~~~~~~~~~ (8) MESSAGE HANDLERS ~~~~~~~~~
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message) -> None:
	first_name: str = message.from_user.first_name
	with open('photos/terminator.jpg', 'rb') as image:
		await bot.send_photo(
			chat_id=message.from_user.id,
			photo=image,
			caption=f"Welcome, {first_name}! Ready to begin? Ask me anything. /help for commands.")


@dp.message_handler(commands=['help'])
async def help_command(message: types.Message) -> None:
	text: str = """
\~\~\~ COMMAND MENU \~\~\~

/help \- Access this help menu\.
/ask\_gemini \- Receive a response from Google's Gemini\.
/ask\_claude \- Receive a response from Anthropic's Claude\.
/translate \- Translate text from one language to another\.
/new\_chat \- Start a new conversation with Google's Gemini\.
/learn\_more \- additional details about Bardtolino

*Accuracy Notice:*
Bardtolino's responses are based on a vast dataset of information\. However, to ensure the highest level of accuracy, please *consider cross\-referencing information* with other reliable sources\.
"""
	await message.reply(text="⭐Update!⭐\n\nIn February 2024, Google's Bard service was changed to Gemini.")
	await message.answer(text=text, parse_mode=types.ParseMode.MARKDOWN_V2)


@dp.message_handler(commands=['learn_more'])
async def learn_more_command(message: types.Message) -> None:
	definitions: str = """
\~\~\~ Definition of terms \~\~\~

\* *Large Language Model*\(LLM\) \- AI system trained on a vast amount of data to understand and generate human language\.
"""
	tools_explanation: str = f"""
\~\~\~ Compiled tools available \~\~\~

*{link("Gemini Pro", "https://gemini.google.com/")}* \- {link("Google", "https://deepmind.google/technologies/gemini/")}'s LLM
\* Capable of providing text responses
\* Can also provide images from the web
\* It can keep your conversation, so you can ask follow\-up questions

*{link("Claude Haiku", "https://claude.ai/")}* \- {link("Anthropic", "https://www.anthropic.com/")}'s LLM
\* Capable of providing text responses

*Text Translator* \- by {link("Terry Yin", "https://pypi.org/user/Terry.Yin/")}
\* Capable of translating simple text with these languages \(English, Filipino, Japanese, Korean, Spanish, and French\)


With those two LLMs, cross\-referencing is possible\. With the help of text translator, user queries can be expressed using English language as this is the most supported language by the LLMs\.
"""
	await message.answer(text=definitions, parse_mode=types.ParseMode.MARKDOWN_V2)
	await message.answer(text=tools_explanation, parse_mode=types.ParseMode.MARKDOWN_V2, disable_web_page_preview=True)


@dp.message_handler(commands=['ask_gemini'])
async def ask_gemini_command(message: types.Message) -> None:
	db.update_selected_tool(connection_pool=connection_pool, user_id=message.from_user.id, value=1)
	await message.answer(text=f"Welcome {message.from_user.first_name}, What would you like to discuss with Gemini? ✨")


@dp.message_handler(commands=['new_chat'])
async def new_chat_command(message: types.Message) -> None:
	db.update_metadata(connection_pool=connection_pool, user_id=message.from_user.id, metadata=None)
	db.update_selected_tool(connection_pool=connection_pool, user_id=message.from_user.id, value=1)
	await message.answer(text="Great! I'm excited about a new and interesting topic 👌")


@dp.message_handler(commands=['translate'])
async def translate_command(message: types.Message) -> None:
	db.update_selected_tool(connection_pool=connection_pool, user_id=message.from_user.id, value=2)
	keyboard = await create_inline_keyboard(callback_data_name="first_lang")
	await message.reply(text="Avisala Eshma!\n\nPlease choose the Original Language:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('first_lang:'))
async def process_first_language(callback_query: types.CallbackQuery) -> None:
	first_lang: str = callback_query.data.split(':')[1]
	db.update_first_language(
		connection_pool=connection_pool, 
		user_id=callback_query.from_user.id, 
		first_language=first_lang)
	keyboard = await create_inline_keyboard(callback_data_name="second_lang", rem_keeb=first_lang)
	await bot.edit_message_text(
		text="Choose the target language:",
		chat_id=callback_query.message.chat.id,
		message_id=callback_query.message.message_id,
		reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('second_lang:'))
async def process_second_language(callback_query: types.CallbackQuery) -> None:
	languages: list[str] = db.update_second_language(
		connection_pool=connection_pool,
		user_id=callback_query.from_user.id,
		second_language=callback_query.data.split(':')[1])
	language_dict: dict = {
	'en': 'English', 'tl': 'Filipino',
	'ja': 'Japanese', 'ko': 'Korean',
	'es': 'Spanish', 'fr': 'French'}
	first_language: str = language_dict[languages[0]]
	second_language: str = language_dict[languages[1]]
	await bot.edit_message_text(
		text=f"Ready to translate {first_language} to {second_language}!\nEnter your text:",
		chat_id=callback_query.message.chat.id,
		message_id=callback_query.message.message_id)


@dp.message_handler(commands=['ask_claude'])
async def ask_claude_command(message: types.Message) -> None:
	db.update_selected_tool(connection_pool=connection_pool, user_id=message.from_user.id, value=3)
	await message.answer(text=f"Welcome {message.from_user.first_name}, What would you like to discuss with Claude AI? ❤")



@dp.message_handler(content_types=[types.ContentType.PHOTO, types.ContentType.TEXT])
async def main(message: types.Message) -> None:
	user_id: int = message.from_user.id
	tool: int = db.selected_tool(connection_pool=connection_pool, user_id=user_id)
	prompt: str = message.text

	print(f"({tool}) {user_id}: {prompt}")

	loading_message = await bot.send_message(chat_id=user_id, text="Processing... ⏳")
	loading_id: int = loading_message.message_id

	match tool:
		case 1: # G E M I N I !
			response: list = []
			if message.content_type == types.ContentType.TEXT:
				response = await ask_gemini(connection_pool, user_id, prompt)
			elif message.content_type == types.ContentType.PHOTO:
				caption = "Describe what's in here" if not message.caption else message.caption
				image = await save_image_from_user(message.photo)
				if image:
					response = await ask_gemini(connection_pool, user_id, caption, image)
					remove(image)
				else:
					await message.reply("Failed to save the image, please retry to send the image.")
					return
			try:
				await bot.edit_message_text(
					text=fix_formatting(response.text),
					chat_id=user_id,
					message_id=loading_id)
				await send_response_image(user_id, response.images, message)
			except Exception as e:
				print(f"\nError occured when sending a response from gemini:\n{e}\n")
				await bot.edit_message_text(
					text="My apologies for the inconvenience, we will temporarily terminate the program to fix it. 💐",
					chat_id=user_id,
					message_id=loading_id)
		case 2: # T R A N S L A T E !
			languages: list[str] = db.selected_languages(connection_pool=connection_pool, user_id=user_id)
			translated_text = translate_text(
				text=prompt, 
				from_language=languages[0], 
				to_language=languages[1])
			text: str = translated_text if translated_text != '' else 'Please provide more context in your text.'
			await bot.edit_message_text(
				chat_id=user_id,
				message_id=loading_id,
				text=text)
		case 3: # C L A U D E !
			response = ask_claude(prompt=prompt)
			await bot.edit_message_text(
				chat_id=user_id,
				message_id=loading_id,
				text=response)


if __name__ == '__main__':
	from aiogram import executor
	executor.start_polling(dp, skip_updates=True)
