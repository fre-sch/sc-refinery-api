PRAGMA foreign_keys=0;
DROP TABLE IF EXISTS "user";
DROP TABLE IF EXISTS "user_perm";
DROP TABLE IF EXISTS "user_session";
DROP TABLE IF EXISTS "station";
DROP TABLE IF EXISTS "ore";
DROP TABLE IF EXISTS "method";
DROP TABLE IF EXISTS "method_ore";
DROP TABLE IF EXISTS "station_ore";
DROP TABLE IF EXISTS "mining_session";
DROP TABLE IF EXISTS "mining_session_user";
DROP TABLE IF EXISTS "mining_session_entry";
PRAGMA foreign_keys=1;

CREATE TABLE "user" (
	"id"	        INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"          TEXT NOT NULL,
	"mail"	        TEXT NOT NULL UNIQUE,
	"is_google"     INTEGER NOT NULL DEFAULT '0',
	"is_active"     INTEGER NOT NULL DEFAULT '0',
	"password_hash" TEXT NOT NULL DEFAULT '',
	"created"   	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	    REAL NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);
CREATE TABLE "user_perm" (
	"user_id"	INTEGER NOT NULL,
	"scope"	    TEXT NOT NULL,
	"created"   REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"   REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	UNIQUE("user_id", "scope")
);
CREATE TABLE "user_session" (
	"user_id"	INTEGER NOT NULL,
	"user_ip"   TEXT NOT NULL,
	"salt"      INTEGER NOT NULL,
	"created"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id")
);
CREATE TABLE "station" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);
CREATE TABLE "ore" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);
CREATE TABLE "method" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);
CREATE TABLE "method_ore" (
	"method_id" INTEGER NOT NULL,
	"ore_id"    INTEGER NOT NULL,
	"efficiency" REAL NOT NULL DEFAULT '0',
	"cost"      REAL NOT NULL DEFAULT '0',
	"duration"  REAL NOT NULL DEFAULT '0',
	"created"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("method_id") REFERENCES "method"("id"),
	FOREIGN KEY("ore_id") REFERENCES "ore"("id"),
	UNIQUE("method_id", "ore_id")
);
CREATE TABLE "station_ore" (
	"station_id"        INTEGER NOT NULL,
	"ore_id"            INTEGER NOT NULL,
	"efficiency_bonus"  REAL NOT NULL DEFAULT '0',
	"created"	        REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	        REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("station_id") REFERENCES "station"("id"),
	FOREIGN KEY("ore_id") REFERENCES "ore"("id"),
	UNIQUE("station_id", "ore_id")
);
CREATE TABLE "mining_session" (
	"id"    	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	        TEXT NOT NULL,
	"is_open"       INTEGER NOT NULL DEFAULT '0',
	"created"   	REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	    REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"closed"	    REAL NOT NULL DEFAULT (DATETIME('now', 'localtime'))
);
CREATE TABLE "mining_session_user" (
	"mining_session_id"	    INTEGER NOT NULL,
	"user_id"       	    INTEGER NOT NULL,
	"created"	            REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("mining_session_id") REFERENCES "mining_session"("id"),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	UNIQUE("mining_session_id", "user_id")
);
CREATE TABLE "mining_session_entry" (
	"id"	            INTEGER PRIMARY KEY AUTOINCREMENT,
	"user_id"           INTEGER NOT NULL,
	"mining_session_id" INTEGER NOT NULL,
	"station_id"	    INTEGER NOT NULL,
	"ore_id"	        INTEGER NOT NULL,
	"method_id"	        INTEGER NOT NULL,
	"amount"	        INTEGER NOT NULL,
	"duration"          INTEGER NOT NULL,
	"created"	        REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	"updated"	        REAL NOT NULL DEFAULT (DATETIME('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id"),
	FOREIGN KEY("mining_session_id") REFERENCES "mining_session"("id"),
	FOREIGN KEY("station_id") REFERENCES "station"("id"),
	FOREIGN KEY("ore_id") REFERENCES "ore"("id"),
	FOREIGN KEY("method_id") REFERENCES "method"("id")
);

INSERT INTO "user" ("name", "mail") VALUES ('admin', 'admin@screfinery.local');
INSERT INTO "user_perm" ("user_id", "scope") SELECT "id", '*' FROM "user";

INSERT INTO "station" ("name") VALUES ('ARC-L1'), ('CRU-L1'), ('HUR-L1'), ('HUR-L2'), ('MIC-L1');
INSERT INTO "ore" ("name") VALUES ('Agricium'), ('Aluminium'), ('Beryl'), ('Bexalite'), ('Borase'), ('Copper'),
    ('Corundum'), ('Diamond'), ('Gold'), ('Hephaestanite'), ('Laranite'), ('Quantanium'), ('Quartz'), ('Taranite'),
    ('Titanium'), ('Tungsten');
INSERT INTO "method" ("name") VALUES ('Cormack'), ('Dinyx Solventation'), ('Electrostarolysis'), ('Ferron Exchange'),
('Gaskin Process'), ('Kazen Winnowing'), ('Pyrometric Chromalysis'), ('Thermonatic Deposition'), ('XCR Reaction');