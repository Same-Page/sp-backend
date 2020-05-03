CREATE TABLE "auth" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"password"	TEXT,
	"user_id"	INTEGER,
	"created"	INTEGER
);


CREATE TABLE "user" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"name"	TEXT,
	"about"	TEXT,
	"create_time"	INTEGER,
	"credit"	INTEGER,
	"has_avatar"	INTEGER,
	"role"	INTEGER,
	"rooms"	TEXT
);

CREATE TABLE "message" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"sender"	INTEGER,
	"receiver"	INTEGER,
	"message"	TEXT,
	"create_time"	INTEGER
);

CREATE TABLE "follow" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user_id"	INTEGER,
	"follower_id"	INTEGER,
	"create_time"	INTEGER,
	"update_time"	INTEGER,
	"active"	INTEGER
);