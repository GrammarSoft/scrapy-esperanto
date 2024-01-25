PRAGMA case_sensitive_like = ON;
PRAGMA foreign_keys = OFF;
PRAGMA journal_mode = WAL;
PRAGMA locking_mode = EXCLUSIVE;
PRAGMA synchronous = OFF;
PRAGMA threads = 4;
PRAGMA trusted_schema = OFF;
PRAGMA page_size = 65535;
VACUUM;
PRAGMA locking_mode = NORMAL;

CREATE TABLE IF NOT EXISTS urls_seen (
	r_url TEXT NOT NULL,

	PRIMARY KEY (r_url)
);

CREATE TABLE IF NOT EXISTS html_pieces (
	r_hash TEXT NOT NULL,
	r_url INTEGER NOT NULL,
	r_piece TEXT NOT NULL,
	r_stamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (r_hash)
);
