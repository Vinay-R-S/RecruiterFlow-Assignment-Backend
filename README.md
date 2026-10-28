# Recruiter Bot

A small backend that stores candidates and jobs and ranks the best matches in both directions.
Built with FastAPI and SQLite. All database access is hand-written SQL through the stdlib
`sqlite3` module (no ORM, no query builder).

## Project layout

| File           | Purpose                                                           |
| -------------- | ----------------------------------------------------------------- |
| `schema.sql`   | Hand-written DDL for all tables                                   |
| `seed.py`      | Seed data from the assignment (15 candidates, 6 jobs); idempotent |
| `main.py`      | FastAPI app, scoring logic and endpoints                          |
| `recruiter.db` | SQLite file, created on first run                                 |

## Run

    pip install fastapi uvicorn
    uvicorn main:app --reload

The DB is created and seeded on startup. To seed manually: `python seed.py`.
Interactive docs are available at http://localhost:8000/docs.

## Endpoints

| Method | Path                       | Description                                        |
| ------ | -------------------------- | -------------------------------------------------- |
| GET    | `/candidates`              | List all candidates                                |
| GET    | `/jobs`                    | List all jobs                                      |
| GET    | `/jobs/{id}/matches`       | Candidates ranked for a job, with score and reason |
| GET    | `/candidates/{id}/matches` | Jobs ranked for a candidate, with score and reason |

Unknown ids return 404.

    curl 127.0.0.1:8000/candidates
    curl 127.0.0.1:8000/jobs
    curl 127.0.0.1:8000/jobs/1/matches
    curl 127.0.0.1:8000/candidates/1/matches

Example response (`/jobs/1/matches`, trimmed):

    {
      "job": "Backend Detective",
      "matches": [
        {
          "candidate_id": 1,
          "name": "Sherlock H.",
          "score": 0.95,
          "reason": "3/3 skills (deduction, forensics, pattern-recognition); 8y vs 3y min; availability: Immediate; culture: analytical"
        }
      ]
    }

## Schema

| Table              | Columns                                   |
| ------------------ | ----------------------------------------- |
| `candidates`       | id, name, experience, availability, quirk |
| `candidate_skills` | candidate_id, skill                       |
| `candidate_traits` | candidate_id, trait                       |
| `jobs`             | id, title, min_experience, tagline        |
| `job_skills`       | job_id, skill                             |
| `job_culture`      | job_id, keyword                           |

Skills, traits and keywords live in their own link tables instead of comma-separated columns,
so overlap can be computed with plain joins or set operations. A "match" is not stored: it is
computed on request, which keeps the data consistent when candidates or jobs change.

## Scoring (0 to 1)

| Factor         | Weight | Rule                                      |
| -------------- | ------ | ----------------------------------------- |
| Skill overlap  | 0.55   | matched required skills / required skills |
| Experience fit | 0.25   | 1.0 if meets min, else experience / min   |
| Culture        | 0.10   | shared traits / culture keywords          |
| Availability   | 0.10   | Immediate 1.0, 2 weeks 0.5, Not looking 0 |

Design notes:

- Skills carry the most weight because they are the core requirement.
- Experience is capped at 1.0, so overqualified candidates are not rewarded beyond the minimum
  and under-qualified ones are penalized proportionally rather than rejected.
- Availability is a soft signal: "Not looking" candidates still appear, just ranked lower.
- Ties are broken alphabetically for stable output.
- Skills are normalized (lowercase, spaces to hyphens) so "stakeholder management" matches
  "stakeholder-management".

## Known limitations

- Weights are hand-picked, not tuned on real hiring outcomes.
- Skill matching is exact; synonyms (for example "sales" vs "selling") are not recognized.
- Traits are compared to culture keywords by exact match only.
- No pagination, auth, or tests.

## Note

- Antigravity (Gemini models) were used in this assignment
- Used in completing the backend assignment
- Used to write the complex SQL queries
