#!/usr/bin/env python3
"""
Fake resume generator
- Produces NUM_CVS PDFs in OUTPUT_DIR
- Uses LM Studio (optional) for better summaries/projects
- Adds random internships
- Random templates and fonts/layouts
"""

import os
import random
import requests
from faker import Faker
from fpdf import FPDF

# =========================
# CONFIG
# =========================
NUM_CVS = 5
OUTPUT_DIR = "fake_cvs"

USE_LM_STUDIO = True
LM_API_URL = "http://localhost:1234/v1/chat/completions"
LM_MODEL_NAME = "gemma-3-4b-it"
LM_TEMPERATURE = 0.65
LM_MAX_TOKENS = 550
LM_TIMEOUT = 40  # seconds

# Fonts that are guaranteed in FPDF core set
FONT_CHOICES = ["Helvetica", "Times", "Courier"]

fake = Faker("en_IN")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# UTILITIES
# =========================

def safe_text(s: str) -> str:
    """
    Make string safe for latin-1 output used by FPDF.
    Replaces non-latin-1 bytes gracefully.
    """
    try:
        return str(s).encode("latin-1", "replace").decode("latin-1")
    except Exception:
        return str(s)

def call_lm_studio(prompt: str) -> str:
    """
    Call LM Studio-like API. Returns raw assistant text or empty string on failure.
    """
    if not USE_LM_STUDIO:
        return ""

    payload = {
        "model": LM_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Produce natural, human-like resume content. Avoid cliché template phrasing."},
            {"role": "user", "content": prompt}
        ],
        "temperature": LM_TEMPERATURE,
        "max_tokens": LM_MAX_TOKENS,
        "stream": False
    }

    try:
        r = requests.post(LM_API_URL, json=payload, timeout=LM_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        # Be defensive about structure
        return data.get("choices", [{}])[0].get("message", {}).get("content", "") or ""
    except Exception as e:
        print("[LM Studio ERROR]", e)
        return ""

# =========================
# RANDOM INTERNSHIP
# =========================

def generate_random_internship():
    roles = [
        "Software Intern", "Backend Intern", "Security Intern",
        "Network Intern", "Web Development Intern", "QA Intern",
        "DevOps Intern", "Data Engineering Intern"
    ]
    companies = [
        "TechNexa Pvt Ltd", "BlueArc Systems", "Cyberloop InfoSec",
        "StackSoft Labs", "Axiom Networks", "PrimeLogic Solutions",
        "InnovaCore Technologies", "Vertex Solutions"
    ]
    descriptions = [
        "Assisted in debugging tasks, wrote utility scripts and documented issues.",
        "Supported engineers in API testing, wrote test cases and analyzed logs.",
        "Contributed to small UI improvements, fixed bugs and implemented minor features.",
        "Reviewed audit logs, helped update reports and prepared incident summaries.",
        "Built automation scripts, contributed to internal tools and participated in code reviews.",
        "Wrote scripts for automating test runs, aided in continuous integration setup."
    ]
    durations = ["6 weeks", "2 months", "3 months", "1 month"]

    return {
        "role": random.choice(roles),
        "company": random.choice(companies),
        "duration": random.choice(durations),
        "desc": random.choice(descriptions)
    }

# =========================
# AI SECTIONS (summary/projects/achievements)
# =========================

def parse_lm_blocks(raw: str):
    """
    Parse LM text expected with markers:
    ===SUMMARY=== ... ===PROJECTS=== ... ===ACHIEVEMENTS=== ...
    Returns dict with summary, projects(list), achievements(list)
    """
    fallback_summary = (
        "Final-year engineering student with hands-on academic projects and internship experience. "
        "Practical with debugging, problem solving and collaborative development."
    )
    fallback_projects = [
        "Attendance Web App - Built a simple full-stack app using Flask, HTML, CSS and JavaScript to record attendance.",
        "Log Analyzer - Python script to parse logs, extract key metrics and generate basic summaries."
    ]
    fallback_achievements = [
        "Ranked in top performers in college coding hackathon.",
        "Completed online coursework in Data Structures and Algorithms."
    ]

    if not raw or "===SUMMARY===" not in raw:
        return {
            "summary": fallback_summary,
            "projects": fallback_projects,
            "achievements": fallback_achievements
        }

    def extract(section):
        try:
            return raw.split(section, 1)[1].split("===", 1)[0].strip()
        except Exception:
            return ""

    summary = extract("===SUMMARY===") or fallback_summary
    projects_block = extract("===PROJECTS===")
    achievements_block = extract("===ACHIEVEMENTS===")

    projects = []
    for line in projects_block.splitlines():
        line = line.strip()
        if not line:
            continue
        # allow lines like "Title - description"
        projects.append(line.lstrip("-• ").strip())

    achievements = []
    for line in achievements_block.splitlines():
        line = line.strip()
        if not line:
            continue
        achievements.append(line.lstrip("-• ").strip())

    if not projects:
        projects = fallback_projects
    if not achievements:
        achievements = fallback_achievements

    return {
        "summary": summary,
        "projects": projects,
        "achievements": achievements
    }

def generate_ai_sections(name, role, skills, college, cgpa):
    """
    Ask LM to produce natural summary, projects and achievements.
    If LM fails, use realistic fallbacks.
    """
    prompt = f"""
Generate resume content in EXACTLY the following structure (do not add or remove sections):

===SUMMARY===
(2-3 natural sentences about the candidate, no clichés)

===PROJECTS===
<Project Title> - <1-2 lines description>
<Project Title> - <1-2 lines description>

===ACHIEVEMENTS===
- <achievement 1>
- <achievement 2>

Candidate details:
Name: {name}
Target role: {role}
Skills: {', '.join(skills)}
College: {college}
CGPA: {cgpa}

Write like a real student would write about their work. Avoid overly formal or 'AI' phrasing.
"""
    raw = call_lm_studio(prompt)
    return parse_lm_blocks(raw)

# =========================
# BASIC RESUME DATA
# =========================

def generate_basic_resume_data():
    name = fake.name()
    phone = fake.phone_number()
    email = fake.email()
    location = f"{fake.city()}, {fake.state()}"

    college = f"{fake.last_name()} Institute of Technology"
    degree = random.choice([
        "B.Tech in Computer Science and Engineering",
        "B.Tech in Information Technology",
        "B.E in Computer Engineering",
        "B.Sc in Computer Science"
    ])
    cgpa = round(random.uniform(6.4, 9.6), 2)
    grad_year = random.choice([2023, 2024, 2025])

    skill_pool = [
        "Python", "Java", "C", "C++", "SQL", "HTML", "CSS", "JavaScript",
        "React", "Node.js", "Linux", "Git", "Docker", "Networking", "Cybersecurity",
        "Machine Learning", "REST APIs", "Data Structures", "Algorithms"
    ]
    skills = random.sample(skill_pool, k=random.randint(6, 10))

    target_roles = [
        "Software Developer",
        "Full Stack Developer",
        "Cybersecurity Analyst",
        "Backend Engineer",
        "Network Engineer",
        "ML Engineer"
    ]
    role = random.choice(target_roles)

    data = {
        "name": name,
        "phone": phone,
        "email": email,
        "location": location,
        "college": college,
        "degree": degree,
        "cgpa": cgpa,
        "grad_year": grad_year,
        "skills": skills,
        "role": role,
        "internship": generate_random_internship()
    }
    return data

# =========================
# PDF / TEMPLATES
# =========================

def choose_template():
    return random.choice(["classic", "sidebar", "minimal"])

class ResumePDF(FPDF):
    def __init__(self, template):
        super().__init__()
        self.template = template
        self.base_font = random.choice(FONT_CHOICES)
        # set slightly variable margins
        left = random.randint(10, 18)
        top = random.randint(10, 18)
        right = random.randint(10, 18)
        self.set_margins(left, top, right)
        # page break and auto-size are fine with defaults

    def header(self):
        # Title header: name
        # Use bold, slightly random size between 15-18
        size = random.choice([15, 16, 17])
        self.set_font(self.base_font, "B", size)
        # Title is set externally via set_title
        self.cell(0, 10, safe_text(self.title), ln=True)

    def section_title(self, title):
        self.ln(2)
        size = random.choice([12, 13, 14])
        self.set_font(self.base_font, "B", size)
        self.cell(0, 7, safe_text(title), ln=True)
        self.set_font(self.base_font, "", 11)

    def add_paragraph(self, text):
        self.set_font(self.base_font, "", 11)
        # use '-' as bullet prefix to keep latin-1 safe
        self.multi_cell(0, 6, safe_text(text))

# =========================
# PDF CREATION
# =========================

def create_pdf(resume, ai_sections, index):
    template = choose_template()
    pdf = ResumePDF(template)
    pdf.set_title(resume["name"])
    pdf.add_page()

    # CONTACT LINE
    contact_line = f"{resume['location']} | {resume['phone']} | {resume['email']}"
    pdf.set_font(pdf.base_font, "", 11)
    pdf.multi_cell(0, 6, safe_text(contact_line))
    pdf.ln(3)

    # TEMPLATES
    if template == "classic":
        pdf.section_title("PROFILE SUMMARY")
        pdf.add_paragraph(ai_sections["summary"])

        pdf.section_title("INTERNSHIP")
        i = resume["internship"]
        pdf.add_paragraph(f"{i['role']} - {i['company']} ({i['duration']})")
        pdf.add_paragraph(f"- {i['desc']}")

        pdf.section_title("EDUCATION")
        pdf.add_paragraph(resume["degree"])
        pdf.add_paragraph(f"{resume['college']} | CGPA: {resume['cgpa']} | Graduated: {resume['grad_year']}")

        pdf.section_title("TECHNICAL SKILLS")
        pdf.add_paragraph(", ".join(resume["skills"]))

        pdf.section_title("PROJECTS")
        for p in ai_sections["projects"]:
            pdf.add_paragraph(f"- {p}")

        pdf.section_title("ACHIEVEMENTS")
        for a in ai_sections["achievements"]:
            pdf.add_paragraph(f"- {a}")

    elif template == "sidebar":
        # Basic two-column effect: write skills in left column as a vertical block,
        # main content in right column. This is a simple approximation — not fancy.
        margin_left = pdf.l_margin
        right_start_x = margin_left + 60  # left column width ~60mm

        # Left column: Skills + basic personal info
        pdf.set_xy(margin_left, 40)
        pdf.set_font(pdf.base_font, "B", 12)
        pdf.cell(55, 6, safe_text("SKILLS"), ln=True)
        pdf.set_font(pdf.base_font, "", 10)
        pdf.set_x(margin_left)
        pdf.multi_cell(55, 5, safe_text("\n".join(resume["skills"])))

        pdf.set_x(margin_left)
        pdf.ln(1)
        pdf.set_font(pdf.base_font, "B", 12)
        pdf.cell(55, 6, safe_text("EDUCATION"), ln=True)
        pdf.set_font(pdf.base_font, "", 10)
        pdf.set_x(margin_left)
        pdf.multi_cell(55, 5, safe_text(f"{resume['degree']}\n{resume['college']}\nCGPA: {resume['cgpa']}"))

        # Right column: summary, internship, projects
        pdf.set_xy(right_start_x, 40)
        pdf.set_font(pdf.base_font, "B", 13)
        pdf.cell(0, 6, safe_text("SUMMARY"), ln=True)
        pdf.set_font(pdf.base_font, "", 11)
        pdf.set_x(right_start_x)
        pdf.multi_cell(0, 6, safe_text(ai_sections["summary"]))

        pdf.set_x(right_start_x)
        pdf.ln(2)
        pdf.set_font(pdf.base_font, "B", 12)
        pdf.cell(0, 6, safe_text("INTERNSHIP"), ln=True)
        i = resume["internship"]
        pdf.set_font(pdf.base_font, "", 11)
        pdf.set_x(right_start_x)
        pdf.multi_cell(0, 6, safe_text(f"{i['role']} - {i['company']} ({i['duration']})\n- {i['desc']}"))

        pdf.set_x(right_start_x)
        pdf.ln(2)
        pdf.set_font(pdf.base_font, "B", 12)
        pdf.cell(0, 6, safe_text("PROJECTS"), ln=True)
        pdf.set_font(pdf.base_font, "", 11)
        pdf.set_x(right_start_x)
        for p in ai_sections["projects"]:
            pdf.multi_cell(0, 6, safe_text(f"- {p}"))

        pdf.set_x(right_start_x)
        pdf.ln(2)
        pdf.set_font(pdf.base_font, "B", 12)
        pdf.cell(0, 6, safe_text("ACHIEVEMENTS"), ln=True)
        pdf.set_font(pdf.base_font, "", 11)
        pdf.set_x(right_start_x)
        for a in ai_sections["achievements"]:
            pdf.multi_cell(0, 6, safe_text(f"- {a}"))

    else:  # minimal
        pdf.section_title("SUMMARY")
        pdf.add_paragraph(ai_sections["summary"])

        pdf.section_title("INTERNSHIP")
        i = resume["internship"]
        pdf.add_paragraph(f"{i['role']} - {i['company']} ({i['duration']})")
        pdf.add_paragraph(f"- {i['desc']}")

        pdf.section_title("PROJECTS")
        for p in ai_sections["projects"]:
            pdf.add_paragraph(f"- {p}")

        pdf.section_title("TECHNICAL SKILLS")
        pdf.add_paragraph(", ".join(resume["skills"]))

        pdf.section_title("EDUCATION")
        pdf.add_paragraph(f"{resume['degree']} | {resume['college']} | CGPA: {resume['cgpa']}")

        pdf.section_title("ACHIEVEMENTS")
        for a in ai_sections["achievements"]:
            pdf.add_paragraph(f"- {a}")

    filename = os.path.join(OUTPUT_DIR, f"cv_{index:03d}.pdf")
    pdf.output(filename)
    print(f"Generated: {filename}  (template={template}, font={pdf.base_font})")

# =========================
# MAIN
# =========================

def main():
    for i in range(1, NUM_CVS + 1):
        data = generate_basic_resume_data()
        ai_sections = generate_ai_sections(
            data["name"],
            data["role"],
            data["skills"],
            data["college"],
            data["cgpa"]
        )
        create_pdf(data, ai_sections, i)

if __name__ == "__main__":
    main()
