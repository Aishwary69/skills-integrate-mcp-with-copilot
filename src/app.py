"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
import sqlite3
from pydantic import BaseModel

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

class SignupRequest(BaseModel):
    email: str

def init_db():
    conn = sqlite3.connect('activities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        name TEXT PRIMARY KEY,
        description TEXT,
        schedule TEXT,
        max_participants INTEGER
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS signups (
        activity_name TEXT,
        email TEXT,
        FOREIGN KEY (activity_name) REFERENCES activities (name)
    )''')
    # Insert initial data if not exists
    c.execute("SELECT COUNT(*) FROM activities")
    if c.fetchone()[0] == 0:
        initial_activities = [
            ("Chess Club", "Learn strategies and compete in chess tournaments", "Fridays, 3:30 PM - 5:00 PM", 12),
            ("Programming Class", "Learn programming fundamentals and build software projects", "Tuesdays and Thursdays, 3:30 PM - 4:30 PM", 20),
            ("Gym Class", "Physical education and sports activities", "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM", 30),
            ("Soccer Team", "Join the school soccer team and compete in matches", "Tuesdays and Thursdays, 4:00 PM - 5:30 PM", 22),
            ("Basketball Team", "Practice and play basketball with the school team", "Wednesdays and Fridays, 3:30 PM - 5:00 PM", 15),
            ("Art Club", "Explore your creativity through painting and drawing", "Thursdays, 3:30 PM - 5:00 PM", 15),
            ("Drama Club", "Act, direct, and produce plays and performances", "Mondays and Wednesdays, 4:00 PM - 5:30 PM", 20),
            ("Math Club", "Solve challenging problems and participate in math competitions", "Tuesdays, 3:30 PM - 4:30 PM", 10),
            ("Debate Team", "Develop public speaking and argumentation skills", "Fridays, 4:00 PM - 5:30 PM", 12)
        ]
        c.executemany("INSERT INTO activities VALUES (?, ?, ?, ?)", initial_activities)
        initial_signups = [
            ("Chess Club", "michael@mergington.edu"),
            ("Chess Club", "daniel@mergington.edu"),
            ("Programming Class", "emma@mergington.edu"),
            ("Programming Class", "sophia@mergington.edu"),
            ("Gym Class", "john@mergington.edu"),
            ("Gym Class", "olivia@mergington.edu"),
            ("Soccer Team", "liam@mergington.edu"),
            ("Soccer Team", "noah@mergington.edu"),
            ("Basketball Team", "ava@mergington.edu"),
            ("Basketball Team", "mia@mergington.edu"),
            ("Art Club", "amelia@mergington.edu"),
            ("Art Club", "harper@mergington.edu"),
            ("Drama Club", "ella@mergington.edu"),
            ("Drama Club", "scarlett@mergington.edu"),
            ("Math Club", "james@mergington.edu"),
            ("Math Club", "benjamin@mergington.edu"),
            ("Debate Team", "charlotte@mergington.edu"),
            ("Debate Team", "henry@mergington.edu")
        ]
        c.executemany("INSERT INTO signups VALUES (?, ?)", initial_signups)
    conn.commit()
    conn.close()

init_db()


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    conn = sqlite3.connect('activities.db')
    c = conn.cursor()
    c.execute("SELECT name, description, schedule, max_participants FROM activities")
    activities = {}
    for row in c.fetchall():
        name, desc, sched, max_p = row
        c2 = conn.cursor()
        c2.execute("SELECT email FROM signups WHERE activity_name = ?", (name,))
        participants = [r[0] for r in c2.fetchall()]
        activities[name] = {
            "description": desc,
            "schedule": sched,
            "max_participants": max_p,
            "participants": participants
        }
    conn.close()
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    conn = sqlite3.connect('activities.db')
    c = conn.cursor()
    c.execute("SELECT max_participants FROM activities WHERE name = ?", (activity_name,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    max_p = row[0]
    c.execute("SELECT COUNT(*) FROM signups WHERE activity_name = ?", (activity_name,))
    count = c.fetchone()[0]
    if count >= max_p:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity is full")
    c.execute("SELECT 1 FROM signups WHERE activity_name = ? AND email = ?", (activity_name, email))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Student is already signed up")
    c.execute("INSERT INTO signups VALUES (?, ?)", (activity_name, email))
    conn.commit()
    conn.close()
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, request: SignupRequest):
    """Unregister a student from an activity"""
    conn = sqlite3.connect('activities.db')
    c = conn.cursor()
    c.execute("DELETE FROM signups WHERE activity_name = ? AND email = ?", (activity_name, request.email))
    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Student {request.email} is not signed up for {activity_name}")
    conn.commit()
    conn.close()
    return {"message": f"Unregistered {request.email} from {activity_name}"}
