import sqlite3

from fastapi import FastAPI, HTTPException

from seed import DB_PATH, seed

app = FastAPI(title="Recruiter Bot")

AVAILABILITY_SCORE = {"immediate": 1.0, "2 weeks": 0.5, "not looking": 0.0}

W_SKILLS = 0.55
W_EXPERIENCE = 0.25
W_CULTURE = 0.10
W_AVAILABILITY = 0.10

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.on_event("startup")
def startup():
    conn = get_conn()
    seed(conn)
    conn.close()

def column_set(conn, sql, param):
    return {row[0] for row in conn.execute(sql, (param,))}

def score(cand, job):
    """cand and job are dicts holding sets and numbers; returns (score, reason)."""
    matched = cand["skills"] & job["skills"]
    skill_ratio = len(matched) / len(job["skills"]) if job["skills"] else 0.0

    if cand["experience"] >= job["min_experience"]:
        exp_fit = 1.0
    else:
        exp_fit = cand["experience"] / job["min_experience"]

    shared_culture = cand["traits"] & job["culture"]
    culture_ratio = len(shared_culture) / len(job["culture"]) if job["culture"] else 0.0

    avail = AVAILABILITY_SCORE.get(cand["availability"].lower(), 0.0)

    total = (
        W_SKILLS * skill_ratio
        + W_EXPERIENCE * exp_fit
        + W_CULTURE * culture_ratio
        + W_AVAILABILITY * avail
    )

    reason = (
        f"{len(matched)}/{len(job['skills'])} skills"
        f" ({', '.join(sorted(matched)) or 'none'}); "
        f"{cand['experience']}y vs {job['min_experience']}y min; "
        f"availability: {cand['availability']}"
    )
    if shared_culture:
        reason += f"; culture: {', '.join(sorted(shared_culture))}"
    return round(total, 3), reason


def load_candidate(conn, row):
    return {
        "id": row["id"],
        "name": row["name"],
        "experience": row["experience"],
        "availability": row["availability"],
        "skills": column_set(conn, "SELECT skill FROM candidate_skills WHERE candidate_id = ?", row["id"]),
        "traits": column_set(conn, "SELECT trait FROM candidate_traits WHERE candidate_id = ?", row["id"]),
    }

def load_job(conn, row):
    return {
        "id": row["id"],
        "title": row["title"],
        "min_experience": row["min_experience"],
        "skills": column_set(conn, "SELECT skill FROM job_skills WHERE job_id = ?", row["id"]),
        "culture": column_set(conn, "SELECT keyword FROM job_culture WHERE job_id = ?", row["id"]),
    }

@app.get("/candidates")
def list_candidates():
    conn = get_conn()
    rows = conn.execute("SELECT id, name, experience, availability FROM candidates ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/jobs")
def list_jobs():
    conn = get_conn()
    rows = conn.execute("SELECT id, title, min_experience FROM jobs ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/jobs/{job_id}/matches")
def job_matches(job_id: int):
    conn = get_conn()
    job_row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if job_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Job not found")
    job = load_job(conn, job_row)

    results = []
    for row in conn.execute("SELECT * FROM candidates").fetchall():
        cand = load_candidate(conn, row)
        s, reason = score(cand, job)
        results.append({"candidate_id": cand["id"], "name": cand["name"], "score": s, "reason": reason})
    conn.close()

    results.sort(key=lambda r: (-r["score"], r["name"]))
    return {"job": job["title"], "matches": results}

@app.get("/candidates/{candidate_id}/matches")
def candidate_matches(candidate_id: int):
    conn = get_conn()
    cand_row = conn.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,)).fetchone()
    if cand_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Candidate not found")
    cand = load_candidate(conn, cand_row)

    results = []
    for row in conn.execute("SELECT * FROM jobs").fetchall():
        job = load_job(conn, row)
        s, reason = score(cand, job)
        results.append({"job_id": job["id"], "title": job["title"], "score": s, "reason": reason})
    conn.close()

    results.sort(key=lambda r: (-r["score"], r["title"]))
    return {"candidate": cand["name"], "matches": results}
