# ~~~~~~~~~~~~~~ SELECT ~~~~~~~~~~~~~~~
def is_user_exist(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT COUNT(id_user) FROM users WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		num = cursor.fetchone()[0]
	return num


def selected_tool(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT selected_tool FROM users WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		tool = cursor.fetchone()[0]
	return tool


def selected_languages(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT first_language, second_language FROM users WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		languages = cursor.fetchall()[0]
	return languages


def select_metadata(connection_pool, user_id):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"SELECT gemini_metadata FROM users WHERE id_user = %s"
		cursor.execute(query, (user_id,))
		gemini_metadata = cursor.fetchone()[0]
	return gemini_metadata


# ~~~~~~~~~~~~~~ INSERT ~~~~~~~~~~~~~~~
def add_user(connection_pool, user_id, username, first_name):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"INSERT INTO users (user_name, name) VALUES (%s, %s)"
		cursor.execute(query, (user_id, username, first_name,))
		connection.commit()


# ~~~~~~~~~~~~~~ UPDATE ~~~~~~~~~~~~~~~
def update_selected_tool(connection_pool, user_id, value):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE users
SET selected_tool = %s
WHERE id_user = %s"""
		cursor.execute(query, (value, user_id,))
		connection.commit()


def update_first_language(connection_pool, user_id, first_language):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE users
SET first_language = %s
WHERE id_user = %s"""
		cursor.execute(query, (first_language, user_id,))
		connection.commit()


def update_second_language(connection_pool, user_id, second_language):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE users
SET second_language = %s
WHERE id_user = %s"""
		cursor.execute(query, (second_language, user_id,))
		connection.commit()

		query1 = f"""
SELECT first_language, second_language 
FROM users 
WHERE id_user = %s"""
		cursor.execute(query1, (user_id,))
		languages = cursor.fetchall()[0]
	return languages


def update_metadata(connection_pool, user_id, metadata):
	with connection_pool.get_connection() as connection:
		cursor = connection.cursor()
		query = f"""
UPDATE users
SET gemini_metadata = %s
WHERE id_user = %s"""
		cursor.execute(query, (metadata, user_id,))
		connection.commit()
