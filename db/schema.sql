

CREATE TABLE "works" (
  id INTEGER PRIMARY KEY,
  folder_path TEXT NOT NULL,
  original_name TEXT NOT NULL,
  image_count INTEGER,
  status TEXT,
  type_id INTEGER REFERENCES types (id),
  title TEXT
);

CREATE TABLE works_draft (
  work_id INTEGER PRIMARY KEY,
  circle_raw TEXT,
  author_raw TEXT,
  source_raw TEXT,
  type_raw TEXT,
  title_raw TEXT,
  note TEXT,
  FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE
);
CREATE TABLE work_circle_authors (
  work_id INTEGER NOT NULL,
  circle_id INTEGER NOT NULL,
  author_id INTEGER, -- NULL可
  PRIMARY KEY (work_id, circle_id, author_id),
  FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE,
  FOREIGN KEY (circle_id) REFERENCES circles (id),
  FOREIGN KEY (author_id) REFERENCES authors (id)
);
CREATE TABLE work_sources (
  work_id INTEGER NOT NULL,
  source_id INTEGER NOT NULL,
  PRIMARY KEY (work_id, source_id),
  FOREIGN KEY (work_id) REFERENCES works (id) ON DELETE CASCADE,
  FOREIGN KEY (source_id) REFERENCES sources (id)
);
CREATE TABLE work_completion_state (
  work_id INTEGER PRIMARY KEY REFERENCES works (id),
  circle_id_done INTEGER,
  author_id_done INTEGER,
  source_id_done INTEGER,
  type_id_done INTEGER,
  title_done BOOLEAN
);

CREATE TABLE circles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE authors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE sources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  type TEXT
);
CREATE TABLE types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS scan_targets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  active BOOLEAN NOT NULL DEFAULT 1,
  note TEXT DEFAULT NULL,
  last_scanned_at TEXT
);
