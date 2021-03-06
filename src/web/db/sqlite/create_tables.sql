PRAGMA encoding = 'UTF-8';

CREATE TABLE "auth" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"password"	TEXT,
	"user_id"	INTEGER,
	"created_at"	INTEGER
);


CREATE TABLE "user" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"name"	TEXT,
	"about"	TEXT,
	"email"	TEXT,
	"website"	TEXT,
	"created_at"	INTEGER,
	"credit"	INTEGER,
	"avatar"	INTEGER,
	"role"	INTEGER,
	"rooms"	TEXT
);

CREATE TABLE "message" (
	"id"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"sender"	INTEGER,
	"receiver"	INTEGER,
	"message"	TEXT,
	"created_at"	INTEGER
);

CREATE TABLE "comment" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user_id"	INTEGER,
	"created_at"	INTEGER,
	"content"	TEXT,
	"url"	TEXT
);


CREATE TABLE "vote" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user_id"	INTEGER,
	"comment_id"	INTEGER,
	"score"	INTEGER
);


CREATE TABLE "follow" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"user_id"	INTEGER,
	"follower_id"	INTEGER,
	"created_at"	INTEGER,
	"updated_at"	INTEGER,
	"active"	INTEGER
);

CREATE TABLE "room" (
	"id"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"owner"	INTEGER,
	"name"	TEXT,
	"about"	TEXT,
	"rules"	TEXT,
	"cover"	INTEGER,
	"background"	INTEGER,
	"active"	INTEGER,
	"created_at"	INTEGER
);