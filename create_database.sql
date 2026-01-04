CREATE DATABASE IF NOT EXISTS my_tg_db;

USE my_tg_db;

CREATE TABLE IF NOT EXISTS quarantine (
	id_user BIGINT UNIQUE, 
	captcha_text VARCHAR(6), 
	input_attempts TINYINT UNSIGNED DEFAULT 3, 
	captcha_attempts TINYINT UNSIGNED DEFAULT 4
);

CREATE TABLE IF NOT EXISTS users (
	id_user BIGINT UNIQUE,
	user_name VARCHAR(32),
	name VARCHAR(50),
	selected_tool TINYINT UNSIGNED DEFAULT 1,
	first_language VARCHAR(2) DEFAULT "en",
	second_language VARCHAR(2) DEFAULT "tl",
	gemini_metadata VARCHAR(150)
);