-- Starter schema for the optional extensions (SQLite or Postgres). Not required by the Applications tab.
-- Every table also carries created_at / updated_at in a real deployment.

CREATE TABLE firm (
  id          INTEGER PRIMARY KEY,
  name        TEXT NOT NULL UNIQUE,
  bucket      TEXT,                 -- kind of employer, ranked in profile.toml
  tier        INTEGER DEFAULT 5,    -- 1 is best
  ats         TEXT,                 -- greenhouse | lever | ashby | other
  slug        TEXT                  -- the board id used by the public API
);

CREATE TABLE posting (
  id          INTEGER PRIMARY KEY,
  firm_id     INTEGER NOT NULL REFERENCES firm(id),
  ext_id      TEXT NOT NULL,        -- the job board's own id
  title       TEXT NOT NULL,
  location    TEXT,
  url         TEXT,
  description TEXT,
  posted_at   TEXT,
  score       REAL,
  UNIQUE (firm_id, ext_id)
);

CREATE TABLE application (
  id          INTEGER PRIMARY KEY,
  posting_id  INTEGER REFERENCES posting(id),   -- NULL for roles found outside the boards
  company     TEXT NOT NULL,
  role        TEXT NOT NULL,
  url         TEXT,
  status      TEXT NOT NULL DEFAULT 'To apply', -- see data-model.md
  applied     TEXT,
  note        TEXT
);

CREATE TABLE contact (
  id          INTEGER PRIMARY KEY,
  firm_id     INTEGER REFERENCES firm(id),
  name        TEXT NOT NULL,
  title       TEXT,
  source      TEXT,                 -- event, alumni, referral, ...
  channel     TEXT,
  stage       TEXT DEFAULT 'target',
  last_touch  TEXT,
  notes       TEXT
);

-- Append-only audit trail: never UPDATE or DELETE rows here.
CREATE TABLE event (
  id          INTEGER PRIMARY KEY,
  entity      TEXT NOT NULL,        -- 'application', 'contact', ...
  entity_id   INTEGER NOT NULL,
  from_state  TEXT,
  to_state    TEXT,
  actor       TEXT,                 -- you | email-scan | agent
  detail      TEXT,                 -- JSON, e.g. the email message id
  at          TEXT NOT NULL
);
