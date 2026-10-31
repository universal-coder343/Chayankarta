"""
Seed data script — Milestone 4 & 5 demo.

Creates 10 sample resumes and 3 sample JDs via the REST API,
suitable for demoing semantic ranking and fairness audit.

Usage
-----
    # Start the backend first:
    cd resume-screening/backend
    uvicorn app.main:app --reload

    # Then in another terminal:
    python scripts/seed_data.py

    # Or with a custom base URL:
    python scripts/seed_data.py --url http://localhost:8000
"""

import argparse
import json
import sys
import time
import urllib.request
import urllib.error


BASE_URL = "http://localhost:8000"


# ---------------------------------------------------------------------------
# Sample Job Descriptions
# ---------------------------------------------------------------------------

JOB_DESCRIPTIONS = [
    {
        "title": "Senior Python Backend Engineer",
        "company": "TechCorp India",
        "raw_text": """
Senior Python Backend Engineer — TechCorp India

We are looking for a Senior Python Backend Engineer to join our growing team.

Required Skills:
- 5+ years of experience in backend development
- Strong proficiency in Python and FastAPI or Django
- Experience with PostgreSQL and MongoDB (NoSQL)
- Docker and Kubernetes experience mandatory
- REST API design and implementation
- Experience with CI/CD pipelines (GitHub Actions, Jenkins)
- Bachelor's degree in Computer Science or related field

Nice to Have:
- Experience with Kafka or RabbitMQ
- AWS or GCP cloud experience
- Knowledge of GraphQL
- Redis caching experience

Responsibilities:
- Design and build scalable microservices
- Collaborate with frontend and ML teams
- Code review and mentorship of junior engineers
""",
    },
    {
        "title": "Machine Learning Engineer",
        "company": "DataDrive Solutions",
        "raw_text": """
Machine Learning Engineer — DataDrive Solutions

Join our AI team to build production ML systems.

Required Skills:
- 3+ years of experience in machine learning
- Proficiency in Python, scikit-learn, and TensorFlow or PyTorch
- Experience with NLP and text processing (spaCy, NLTK, Transformers)
- Strong knowledge of data preprocessing and feature engineering
- SQL and NoSQL databases
- Bachelor's or Master's degree in Computer Science, Mathematics, or Statistics

Preferred:
- Experience with MLflow or Kubeflow
- Knowledge of embedding models and vector databases
- AWS SageMaker or Google Vertex AI
- Publications or Kaggle competition experience

What you'll do:
- Build and deploy ML models at scale
- Design and maintain ML pipelines
- Work closely with data engineers and product teams
""",
    },
    {
        "title": "Full-Stack Developer (React + Node.js)",
        "company": "WebStart Startup",
        "raw_text": """
Full-Stack Developer — WebStart Startup

We need a versatile full-stack developer to build our SaaS product.

Required Skills:
- 2+ years of full-stack development experience
- Strong JavaScript and TypeScript skills
- React.js for frontend development
- Node.js or Express for backend
- PostgreSQL or MySQL database experience
- REST API development and integration
- Git version control

Nice to Have:
- Experience with Next.js or Vite
- Docker and basic DevOps knowledge
- GraphQL experience
- AWS or Firebase experience
- Knowledge of testing frameworks (Jest, Pytest)

Education: Bachelor's degree in Computer Science or equivalent
""",
    },
]


# ---------------------------------------------------------------------------
# Sample Resumes (diverse profiles for ranking + fairness demo)
# ---------------------------------------------------------------------------

RESUMES = [
    # Strong match for Python Backend JD
    {
        "filename": "arjun_sharma_backend.pdf",
        "text": """Arjun Sharma
arjun.sharma@gmail.com | +91 98765 43210 | Bangalore, India

SUMMARY
Backend Engineer with 7 years of experience building scalable systems.

SKILLS
Python, FastAPI, Django, PostgreSQL, MongoDB, Docker, Kubernetes, Redis,
AWS, CI/CD, GitHub Actions, REST APIs, Microservices, Git, Linux

EXPERIENCE
Senior Backend Engineer — MegaTech Pvt Ltd (2020–Present)
- Built microservices with FastAPI serving 10M+ requests/day
- Managed PostgreSQL clusters and MongoDB Atlas
- Led Docker/Kubernetes migration reducing infra costs by 30%

Backend Engineer — StartupXYZ (2017–2020)
- Developed Django REST APIs for e-commerce platform
- Implemented CI/CD pipelines with Jenkins

EDUCATION
B.Tech in Computer Science — IIT Bombay, 2017

CERTIFICATIONS
AWS Certified Solutions Architect
""",
    },
    # Strong match for ML Engineer JD
    {
        "filename": "priya_mehta_ml.pdf",
        "text": """Priya Mehta
priya.mehta@outlook.com | +91 87654 32109 | Hyderabad, India

SUMMARY
Machine Learning Engineer with 4 years specialising in NLP and deep learning.

SKILLS
Python, TensorFlow, PyTorch, scikit-learn, spaCy, Transformers, BERT, NLP,
SQL, MongoDB, Docker, AWS SageMaker, MLflow, Pandas, NumPy, Jupyter

EXPERIENCE
ML Engineer — AI Labs India (2021–Present)
- Built production NLP pipelines for text classification (BERT fine-tuning)
- Deployed models on AWS SageMaker with 99.5% uptime
- Used MLflow for experiment tracking

Data Scientist — Analytics Corp (2020–2021)
- Developed recommendation engine using collaborative filtering

EDUCATION
M.Tech in Data Science — IIT Delhi, 2020

CERTIFICATIONS
Google Professional ML Engineer
""",
    },
    # Good match for Full-Stack JD
    {
        "filename": "rahul_verma_fullstack.pdf",
        "text": """Rahul Verma
rahul.verma@gmail.com | +91 76543 21098 | Mumbai, India

SUMMARY
Full-Stack Developer with 3 years building web applications.

SKILLS
JavaScript, TypeScript, React, Next.js, Node.js, Express, PostgreSQL,
MongoDB, REST APIs, Git, Docker, Jest, Tailwind CSS, Vite

EXPERIENCE
Full-Stack Developer — WebDev Agency (2022–Present)
- Built React + Next.js applications for 5+ clients
- Developed Node.js REST APIs with PostgreSQL backend
- Containerized applications with Docker

Junior Developer — FreelanceProjects (2021–2022)
- React and JavaScript web development

EDUCATION
B.E. in Information Technology — Mumbai University, 2021
""",
    },
    # Moderate match — Python developer, less experience
    {
        "filename": "neha_joshi_python.pdf",
        "text": """Neha Joshi
neha.joshi@yahoo.com | Pune, India

SUMMARY
Software Developer with 2 years of Python and web development.

SKILLS
Python, Django, MySQL, HTML, CSS, JavaScript, Git, Linux, REST APIs

EXPERIENCE
Software Developer — SoftSolutions (2022–Present)
- Developed Django web applications
- Managed MySQL databases and wrote SQL queries

Intern — TechIntern Co (2021)
- Assisted in Python script development

EDUCATION
B.Sc. Computer Science — Pune University, 2022
""",
    },
    # Weak match for Backend JD (different domain)
    {
        "filename": "amit_kumar_finance.pdf",
        "text": """Amit Kumar
amit.kumar@email.com | Delhi, India

SUMMARY
Financial Analyst with 5 years in investment banking and data analysis.

SKILLS
Excel, PowerPoint, SQL, Bloomberg, Financial Modelling, SAP, VBA,
Tableau, Python (basic), Data Analysis

EXPERIENCE
Financial Analyst — Global Bank Ltd (2019–Present)
- Built financial models in Excel and VBA
- Prepared quarterly reports for senior management

Junior Analyst — FinCorp India (2018–2019)
- Data entry and basic SQL reporting

EDUCATION
MBA (Finance) — Delhi University, 2018
Bachelor's in Commerce — Delhi University, 2016
""",
    },
    # Strong ML match, male-proxy name
    {
        "filename": "vikram_singh_ml.pdf",
        "text": """Vikram Singh
vikram.singh@protonmail.com | +91 95678 12345 | Chennai, India

SUMMARY
He is an AI/ML researcher with 5 years of experience in deep learning.
He has published 3 research papers in NLP.

SKILLS
Python, PyTorch, TensorFlow, Keras, scikit-learn, NLP, Transformers,
Hugging Face, spaCy, SQL, Docker, Kubernetes, AWS, MLflow, FastAPI

EXPERIENCE
Senior ML Engineer — NeuroTech Labs (2021–Present)
- Developed transformer-based NLP models (BERT, GPT fine-tuning)
- Built ML pipelines with Kubeflow on GCP

ML Research Engineer — AI Research Institute (2019–2021)
- Published papers on text classification and entity recognition
- Contributed to open-source NLP libraries

EDUCATION
M.S. in Computer Science — IIT Madras, 2019
""",
    },
    # Good Full-Stack, female-proxy signals
    {
        "filename": "sneha_patel_frontend.pdf",
        "text": """Sneha Patel
sneha.patel@gmail.com | Ahmedabad, India

SUMMARY
She is a passionate Front-End Developer with 4 years of experience.
Her expertise lies in React and modern JavaScript development.

SKILLS
JavaScript, TypeScript, React, Redux, Next.js, Vite, HTML5, CSS3,
Tailwind CSS, Node.js, REST APIs, GraphQL, Git, Jest, Figma

EXPERIENCE
Frontend Developer — UITech Solutions (2021–Present)
- Built responsive React SPAs used by 50K+ users
- Implemented GraphQL client integrations
- Mentored 2 junior developers

Junior Frontend Developer — DesignStudio (2020–2021)
- HTML/CSS/JavaScript development

EDUCATION
BCA — Gujarat University, 2020
""",
    },
    # Mid-level, diverse background
    {
        "filename": "rohan_das_devops.pdf",
        "text": """Rohan Das
rohan.das@engineer.com | Kolkata, India

SUMMARY
DevOps Engineer with 4 years of experience in cloud infrastructure.

SKILLS
Docker, Kubernetes, AWS, Terraform, Ansible, CI/CD, Jenkins, GitHub Actions,
Linux, Bash, Python, Monitoring (Prometheus, Grafana), Nginx, PostgreSQL

EXPERIENCE
DevOps Engineer — CloudSystems India (2020–Present)
- Managed AWS infrastructure for 20+ microservices
- Built Terraform IaC for multi-region deployments
- Set up CI/CD pipelines with Jenkins and GitHub Actions

System Administrator — IT Services Ltd (2019–2020)
- Linux server management and monitoring

EDUCATION
B.Tech — West Bengal University of Technology, 2019
""",
    },
    # Senior, broad experience, matches backend JD well
    {
        "filename": "kiran_reddy_senior.pdf",
        "text": """Kiran Reddy
kiran.reddy@techmail.in | +91 99001 23456 | Hyderabad, India

SUMMARY
Software Architect with 10+ years of experience.

SKILLS
Python, Java, FastAPI, Spring Boot, PostgreSQL, MongoDB, Redis, Kafka,
Docker, Kubernetes, AWS, GCP, CI/CD, REST APIs, GraphQL, Microservices,
System Design, Agile, Scrum

EXPERIENCE
Software Architect — Enterprise Software Co (2018–Present)
- Designed distributed microservices handling 50M+ events/day
- Led migration from monolith to Kubernetes microservices
- Mentored team of 15 engineers

Senior Engineer — ProductTech (2014–2018)
- Built Python + Django backend for SaaS product
- Implemented Kafka event streaming pipelines

EDUCATION
M.Tech — BITS Pilani, 2014
""",
    },
    # Entry-level fresh graduate
    {
        "filename": "divya_nair_fresher.pdf",
        "text": """Divya Nair
divya.nair@student.edu | Kochi, India

SUMMARY
Recent Computer Science graduate eager to start career in software development.

SKILLS
Python, JavaScript, React, HTML, CSS, SQL, Git, Data Structures, Algorithms,
Machine Learning (coursework), Pandas, NumPy

EXPERIENCE
Intern — TechStartup Kerala (Jun–Aug 2024)
- Developed React components for internal dashboard
- Wrote Python scripts for data processing

PROJECTS
- Resume Classifier: Built ML model for resume categorisation (Python, scikit-learn)
- College ERP: Full-stack web app using Django and React

EDUCATION
B.Tech in Computer Science — NIT Calicut, 2024 (CGPA: 8.7)

CERTIFICATIONS
Google Data Analytics Certificate
""",
    },
]


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _post(url: str, data: dict) -> dict:
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  HTTP {exc.code}: {body[:200]}")
        return {}


def _get(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        print(f"  HTTP {exc.code}: {body[:200]}")
        return {}


def _upload_resume(base_url: str, filename: str, text: str) -> dict | None:
    """Upload a resume as a text file via multipart form."""
    import io
    import email.generator as gen

    boundary = "----FormBoundary7MA4YWxkTrZu0gW"
    body_parts = []
    body_parts.append(f"--{boundary}".encode())
    body_parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode()
    )
    body_parts.append(b"Content-Type: application/pdf")
    body_parts.append(b"")
    body_parts.append(text.encode("utf-8"))
    body_parts.append(f"--{boundary}--".encode())
    body = b"\r\n".join(body_parts)

    req = urllib.request.Request(
        f"{base_url}/api/resumes/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_resp = exc.read().decode()
        if exc.code == 409:
            print(f"  ⚠  Resume '{filename}' already exists, skipping.")
        else:
            print(f"  HTTP {exc.code}: {body_resp[:200]}")
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Seed demo data for Resume Screening API")
    parser.add_argument("--url", default=BASE_URL, help="Base URL of the API")
    parser.add_argument("--skip-resumes", action="store_true", help="Skip resume upload")
    parser.add_argument("--skip-jds", action="store_true", help="Skip JD creation")
    args = parser.parse_args()

    base = args.url.rstrip("/")

    # Check health
    print(f"🔍 Checking API health at {base}/health ...")
    health = _get(f"{base}/health")
    if not health or health.get("status") != "ok":
        print(f"❌ API not healthy: {health}. Start the backend and try again.")
        sys.exit(1)
    print(f"✅ API is healthy. DB: {health.get('db')}")
    print()

    # --- Create JDs ---
    jd_ids: list[str] = []
    if not args.skip_jds:
        print("📋 Creating Job Descriptions ...")
        for jd in JOB_DESCRIPTIONS:
            print(f"  → {jd['title']} @ {jd['company']} ... ", end="", flush=True)
            result = _post(f"{base}/api/jds/", jd)
            if result.get("id"):
                jd_ids.append(result["id"])
                print(f"✅ id={result['id']}")
            else:
                print("⚠  skipped")
        print()

    # --- Upload resumes ---
    if not args.skip_resumes:
        print("📄 Uploading sample resumes ...")
        for r in RESUMES:
            print(f"  → {r['filename']} ... ", end="", flush=True)
            result = _upload_resume(base, r["filename"], r["text"])
            if result and result.get("id"):
                print(f"✅ id={result['id']}")
            time.sleep(0.2)  # small delay to avoid hammering
        print()

    # --- Backfill embeddings ---
    print("🔢 Backfilling embeddings (this may take 30–60s on first run) ...")
    result = _post(f"{base}/api/rankings/backfill", {})
    print(f"  Embedded: {result.get('embedded', '?')} documents")
    print()

    # --- Quick ranking demo ---
    if jd_ids:
        print(f"🏆 Running ranking demo against JD id={jd_ids[0]} ...")
        result = _get(f"{base}/api/rankings/?jd_id={jd_ids[0]}&top_k=5")
        rankings = result.get("rankings", [])
        if rankings:
            print(f"  Top 5 candidates for '{result.get('jd_title')}':")
            for r in rankings:
                print(
                    f"    #{r['rank']} {r.get('candidate_name', r['filename']):<25} "
                    f"score={r['final_score']:.1f}  "
                    f"matched={r['breakdown']['matched_skills']}"
                )
        print()

        # --- Fairness audit demo ---
        print("⚖  Running fairness audit ...")
        audit = _get(f"{base}/api/audit/fairness?jd_id={jd_ids[0]}&threshold=50")
        print(f"  Total candidates: {audit.get('total_candidates', '?')}")
        print(f"  Disparate Impact Ratio: {audit.get('disparate_impact_ratio', 'N/A')}")
        print(f"  4/5 Rule: {'PASS ✅' if audit.get('passes_four_fifths_rule') else 'FAIL ❌' if audit.get('passes_four_fifths_rule') is False else 'N/A'}")
        print(f"  Summary: {audit.get('summary', '')}")
        print()

    print("✨ Seed data complete!")


if __name__ == "__main__":
    main()
