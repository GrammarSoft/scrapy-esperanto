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


CREATE TABLE IF NOT EXISTS sc_queue (
	q_url TEXT NOT NULL,
	q_stamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (q_url)
);


CREATE TABLE IF NOT EXISTS sc_queue_not (
	q_url TEXT NOT NULL,
	q_stamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (q_url)
);


CREATE TABLE IF NOT EXISTS sc_results (
	r_hash TEXT NOT NULL,
	r_url TEXT NOT NULL,
	r_headers TEXT NOT NULL,
	r_body TEXT NOT NULL,
	r_stamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

	PRIMARY KEY (r_hash)
);
CREATE INDEX IF NOT EXISTS sc_results_r_url ON sc_results (r_url);
