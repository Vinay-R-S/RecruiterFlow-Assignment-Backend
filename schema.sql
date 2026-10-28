CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    experience INTEGER NOT NULL,
    availability TEXT NOT NULL,
    quirk TEXT
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    skill TEXT NOT NULL,
    PRIMARY KEY (candidate_id, skill)
);

CREATE TABLE IF NOT EXISTS candidate_traits (
    candidate_id INTEGER NOT NULL REFERENCES candidates(id),
    trait TEXT NOT NULL,
    PRIMARY KEY (candidate_id, trait)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    min_experience INTEGER NOT NULL,
    tagline TEXT
);

CREATE TABLE IF NOT EXISTS job_skills (
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    skill TEXT NOT NULL,
    PRIMARY KEY (job_id, skill)
);

CREATE TABLE IF NOT EXISTS job_culture (
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    keyword TEXT NOT NULL,
    PRIMARY KEY (job_id, keyword)
);
