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
DROP TABLE IF EXISTS "mining_session_balance";
PRAGMA foreign_keys=1;

CREATE TABLE "user" (
	"id"	        INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"          TEXT NOT NULL,
	"mail"	        TEXT NOT NULL UNIQUE,
	"is_google"     INTEGER NOT NULL DEFAULT '0',
	"is_active"     INTEGER NOT NULL DEFAULT '0',
	"password_hash" TEXT NOT NULL DEFAULT '',
	"created"   	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	    REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"last_login"    REAL NOT NULL DEFAULT (julianday('now', 'localtime'))
);
CREATE TABLE "user_perm" (
	"user_id"	INTEGER NOT NULL,
	"scope"	    TEXT NOT NULL,
	"created"   REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"   REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id") ON DELETE CASCADE,
	UNIQUE("user_id", "scope")
);
CREATE TABLE "user_session" (
	"user_id"	INTEGER NOT NULL,
	"user_ip"   TEXT NOT NULL,
	"salt"      INTEGER NOT NULL,
	"created"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id") ON DELETE CASCADE
);
CREATE TABLE "station" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (julianday('now', 'localtime'))
);
CREATE TABLE "ore" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (julianday('now', 'localtime'))
);
CREATE TABLE "method" (
	"id"	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"name"	    TEXT NOT NULL UNIQUE,
	"created"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (julianday('now', 'localtime'))
);
CREATE TABLE "method_ore" (
	"method_id" INTEGER NOT NULL,
	"ore_id"    INTEGER NOT NULL,
	"efficiency" REAL NOT NULL DEFAULT '0',
	"cost"      REAL NOT NULL DEFAULT '0',
	"duration"  REAL NOT NULL DEFAULT '0',
	"created"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("method_id") REFERENCES "method"("id") ON DELETE CASCADE,
	FOREIGN KEY("ore_id") REFERENCES "ore"("id") ON DELETE CASCADE
);
CREATE TABLE "station_ore" (
	"station_id"        INTEGER NOT NULL,
	"ore_id"            INTEGER NOT NULL,
	"efficiency_bonus"  REAL NOT NULL DEFAULT '0',
	"created"	        REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	        REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("station_id") REFERENCES "station"("id") ON DELETE CASCADE,
	FOREIGN KEY("ore_id") REFERENCES "ore"("id") ON DELETE CASCADE,
	UNIQUE("station_id", "ore_id")
);
CREATE TABLE "mining_session" (
	"id"    	    INTEGER PRIMARY KEY AUTOINCREMENT,
	"creator_id"    INTEGER NULL,
	"name"	        TEXT NOT NULL,
	"is_archived"   INTEGER NOT NULL DEFAULT '0',
	"created"   	REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	    REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"archived"	    REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"yield_scu"     REAL NOT NULL DEFAULT '0',
	"yield_uec"     REAL NOT NULL DEFAULT '0',
	FOREIGN KEY ("creator_id") REFERENCES "user"("id") ON DELETE SET NULL
);
CREATE TABLE "mining_session_user" (
	"mining_session_id"	    INTEGER NOT NULL,
	"user_id"       	    INTEGER NULL,
	"created"	            REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("mining_session_id") REFERENCES "mining_session"("id") ON DELETE CASCADE,
	FOREIGN KEY("user_id") REFERENCES "user"("id") ON DELETE SET NULL,
	UNIQUE("mining_session_id", "user_id")
);
CREATE TABLE "mining_session_entry" (
	"id"	            INTEGER PRIMARY KEY AUTOINCREMENT,
	"mining_session_id" INTEGER NOT NULL,
	"user_id"           INTEGER NULL,
	"station_id"	    INTEGER NOT NULL,
	"ore_id"	        INTEGER NOT NULL,
	"method_id"	        INTEGER NOT NULL,
	"amount"	        INTEGER NOT NULL,
	"duration"          INTEGER NOT NULL,
	"created"	        REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	"updated"	        REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
	FOREIGN KEY("user_id") REFERENCES "user"("id") ON DELETE SET NULL,
	FOREIGN KEY("mining_session_id") REFERENCES "mining_session"("id") ON DELETE CASCADE,
	FOREIGN KEY("station_id") REFERENCES "station"("id"),
	FOREIGN KEY("ore_id") REFERENCES "ore"("id"),
	FOREIGN KEY("method_id") REFERENCES "method"("id")
);
CREATE TABLE "mining_session_balance" (
    "mining_session_id"     INTEGER NULL,
    "sender_user_id"        INTEGER NULL,
    "recipient_user_id"     INTEGER NULL,
    "outstanding_amount"    INTEGER NOT NULL,
    "paid_amount"           INTEGER NOT NULL,
    "created"	            REAL NOT NULL DEFAULT (julianday('now', 'localtime')),
    FOREIGN KEY("mining_session_id") REFERENCES "mining_session"("id") ON DELETE SET NULL,
	FOREIGN KEY("sender_user_id") REFERENCES "user"("id") ON DELETE SET NULL,
	FOREIGN KEY("recipient_user_id") REFERENCES "user"("id") ON DELETE SET NULL
);

INSERT INTO "station" ("name") VALUES ('ARC-L1'), ('CRU-L1'), ('HUR-L1'), ('HUR-L2'), ('MIC-L1');
INSERT INTO "ore" ("name") VALUES ('Agricium'), ('Aluminium'), ('Beryl'), ('Bexalite'), ('Borase'), ('Copper'),
    ('Corundum'), ('Diamond'), ('Gold'), ('Hephaestanite'), ('Laranite'), ('Quantanium'), ('Quartz'), ('Taranite'),
    ('Titanium'), ('Tungsten');
INSERT INTO "method" ("name") VALUES ('Cormack'), ('Dinyx Solventation'), ('Electrostarolysis'), ('Ferron Exchange'),
('Gaskin Process'), ('Kazen Winnowing'), ('Pyrometric Chromalysis'), ('Thermonatic Deposition'), ('XCR Reaction');
