# ~~~~~~~~~~~~~~ SELECT ~~~~~~~~~~~~~~~
def is_user_exist(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT COUNT(id_user) FROM quarantine WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		num = cursor.fetchone()[0]
	return num


def get_user(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT * FROM quarantine WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		user = cursor.fetchall()[0]
	return user


def get_captcha_attempts(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT captcha_attempts FROM quarantine WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		num_of_captcha_attemps = cursor.fetchone()[0]
	return num_of_captcha_attemps


def get_captcha_text(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT captcha_text FROM quarantine WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		captcha_text = cursor.fetchone()[0]
	return captcha_text


# ~~~~~~~~~~~~~~ INSERT ~~~~~~~~~~~~~~~
def add_user(connection_pool, user_id, captcha_text):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"INSERT INTO quarantine (id_user, captcha_text) VALUES (%s, %s)"
		cursor.execute(query, (user_id, captcha_text,))
		connection.commit()


def verified(connection_pool, user_id, username, first_name):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		qu_ery = f"""
INSERT INTO users (id_user, user_name, name)
VALUE (%s, %s, %s)"""
		cursor.execute(qu_ery, (user_id, username, first_name))
		query = f"""
UPDATE quarantine 
SET captcha_attempts = 0, input_attempts = 0
WHERE id_user = %s"""
		cursor.execute(query, (user_id,))
		connection.commit()


# ~~~~~~~~~~~~~~ UPDATE ~~~~~~~~~~~~~~~
def another_captcha(connection_pool, user_id, captcha_text):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE quarantine
SET captcha_text = %s, input_attempts = 3, captcha_attempts = captcha_attempts - 1
WHERE id_user = %s"""
		cursor.execute(query, (captcha_text, user_id,))
		connection.commit()


def decrement_input_attempts(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE quarantine
SET input_attempts = input_attempts - 1
WHERE id_user = %s"""
		cursor.execute(query, (user_id,))
		connection.commit()
