CREATE TABLE IF NOT EXISTS DataTypes (
	id_type INTEGER PRIMARY KEY AUTOINCREMENT,
	definition TEXT UNIQUE NOT NULL
);


CREATE TABLE IF NOT EXISTS Status (
	id_status INTEGER PRIMARY KEY AUTOINCREMENT,
	definition TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS StanForD_Records (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	abatteuse TEXT NOT NULL,
	date DATETIME NOT NULL,
	pathJson TEXT UNIQUE NOT NULL,
	id_status INTEGER NOT NULL,
	id_type INTEGER NOT NULL,
	FOREIGN KEY (id_type) REFERENCES DataTypes(id_type) ON DELETE CASCADE
	FOREIGN KEY (id_status) REFERENCES Status(id_status) ON DELETE CASCADE
);

INSERT INTO Status (definition) VALUES
	("local"),
	("phone"),
	("cloud"),
	("to_be_deleted");

INSERT INTO DataTypes (definition) VALUES
	("static_header"),
	("dynamic_header"),
	("data");
