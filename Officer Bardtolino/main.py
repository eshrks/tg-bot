import os
import secrets
import database as db
from dotenv import load_dotenv
from string import ascii_letters
from mysql.connector import pooling
from captcha.image import ImageCaptcha
from aiogram import Bot, Dispatcher, types

load_dotenv()

bot = Bot(os.getenv('RUBIKSCUBE'))
dp = Dispatcher(bot)

connection_pool = pooling.MySQLConnectionPool(
	pool_name=os.getenv('COL_6'),
	host=os.getenv('HORSE'),
	port=int(os.getenv('PURGE')),
	user=os.getenv('SUPERBOOK'),
	password=os.getenv('SUPERPOWER'),
	database=os.getenv('DRUM')
	)

captcha = ImageCaptcha(
	fonts=['assets/fonts/consola.ttf'],
	width=400,
	height=160,
	font_sizes=(63, 65)
	)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
	user_id = message.from_user.id
	captcha_text = ''.join(secrets.choice(ascii_letters) for _ in range(6)).lower()
	user = db.is_user_exist(connection_pool=connection_pool, user_id=user_id)

	match user:
		case 1: # User Exists
			remaining_attempts = db.get_captcha_attempts(connection_pool=connection_pool, user_id=user_id)
			if remaining_attempts > 0:
				db.another_captcha(connection_pool=connection_pool, user_id=user_id, captcha_text=captcha_text)
			else:
				return
		case 0: # New User
			db.add_user(connection_pool=connection_pool, user_id=user_id, captcha_text=captcha_text)

	captcha_text = db.get_captcha_text(connection_pool=connection_pool, user_id=user_id)
	file_name = f'{captcha_text}.png'

	captcha.write(captcha_text, file_name)

	with open(file_name, 'rb') as image:
		await bot.send_photo(
			chat_id=user_id,
			photo=image,
			caption="Type the characters as shown above:")
		os.remove(file_name)


@dp.message_handler()
async def brave_guard(message: types.Message):
	user_id = message.from_user.id
	user = db.get_user(connection_pool=connection_pool, user_id=user_id)
	remaining_attempts = user[3]
	input_attempts = user[2]
	user_input = message.text.lower()

	if remaining_attempts == 0 and input_attempts == 0: # BANNED
		return
	else: # VERIFYING
		captcha_text = user[1]
		if user_input != captcha_text and input_attempts == 1 and remaining_attempts == 0:
			db.decrement_input_attempts(connection_pool=connection_pool, user_id=user_id)
			await message.answer(text="Enough.")
			return
		elif user_input != captcha_text and input_attempts == 1:
			db.decrement_input_attempts(connection_pool=connection_pool, user_id=user_id)
			await message.answer(text="You mispelled 3 times. Please verify again using /start")
		elif user_input != captcha_text and input_attempts > 0:
			db.decrement_input_attempts(connection_pool=connection_pool, user_id=user_id)
			await message.answer(text="❌ Nah uh, try again.")
		elif user_input == captcha_text and input_attempts > 0:
			db.verified(
				connection_pool=connection_pool,
				user_id=user_id,
				username=message.from_user.username,
				first_name=message.from_user.first_name)
			await message.answer(text=f"Yay! you can now message {os.getenv('UN')} 😎")


if __name__ == '__main__':
	from aiogram import executor
	executor.start_polling(dp, skip_updates=True)
