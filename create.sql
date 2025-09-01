DROP TABLE words;
CREATE TABLE IF NOT EXISTS words (
	word_id SERIAL PRIMARY KEY,
	ru VARCHAR(20) UNIQUE
);

INSERT INTO words (ru) VALUES
	('мир'),
	('я'),
	('ты'),
	('он'),
	('она'),
	('мы'),
	('белый'),
	('черный'),
	('желтый'),
	('зеленый');

/*INSERT INTO words (ru) VALUES
	('новый'),
	('проверка');
SELECT * FROM words;*/

DROP TABLE translates;
CREATE TABLE IF NOT EXISTS translates (
	translate_id SERIAL UNIQUE/*PRIMARY KEY*/,
	en VARCHAR(20) NOT NULL,
	word_id INTEGER NOT NULL REFERENCES words(word_id),
	CONSTRAINT pk PRIMARY KEY (word_id, en)
);

INSERT INTO translates (en, word_id) VALUES
	('peace', 1),
	('me', 2),
	('you', 3),
	('he', 4),
	('she', 5),
	('we', 6),
	('white', 7),
	('black', 8),
	('yellow', 9),
	('green', 10);
/*
INSERT INTO translates (en, word_id) VALUES
	('new', 11),
	('test', 12),
	('check', 12);
INSERT INTO translates (en, word_id) VALUES
	('world', 1);
SELECT * FROM translates;
*/

DROP TABLE users_translates;
CREATE TABLE IF NOT EXISTS users_translates (
	user_id INTEGER NOT NULL,
	--deleted boolean NOT NULL default false,
	translate_id INTEGER NOT NULL REFERENCES translates(translate_id),
	CONSTRAINT ut_pk PRIMARY KEY (user_id, translate_id)
);
INSERT INTO users_translates  (user_id, translate_id) VALUES 
(0, 1),
(0, 2),
(0, 3),
(0, 4),
(0, 5),
(0, 6),
(0, 7),
(0, 8),
(0, 9),
(0, 10);
/*
INSERT INTO users_translates  (user_id, translate_id) VALUES 
(2, 12);
INSERT INTO users_translates (user_id, translate_id) VALUES 
(2, 14);
INSERT INTO users_translates (user_id, translate_id) VALUES 
(2, 13);

SELECT * FROM users_translates 
*/
DROP TABLE deleted;
CREATE TABLE IF NOT EXISTS deleted (
	user_id INTEGER NOT NULL,
	word_id INTEGER NOT NULL REFERENCES words(word_id),
	CONSTRAINT dl_pk PRIMARY KEY (user_id, word_id)
);
/*
INSERT INTO deleted (user_id, word_id) VALUES
	(2, 2);
*/
