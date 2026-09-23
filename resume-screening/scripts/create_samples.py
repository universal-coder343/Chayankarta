"""
Generate synthetic sample resumes and job descriptions for testing.

Creates:
  - 2 text PDFs (reportlab)
  - 1 DOCX (python-docx)
  - 1 scanned-image PNG (Pillow)
  - 1 messy-layout PDF (reportlab, multi-column)
  - 3 job description .txt files

All data is synthetic/fake — no real people's information.

Usage:
    pip install reportlab python-docx Pillow
    python scripts/create_samples.py
"""

import os
import textwrap

# ---------------------------------------------------------------------------
# Synthetic resume data (all fake)
# ---------------------------------------------------------------------------

RESUME_JOHN_DOE = textwrap.dedent("""\
    John Doe
    john.doe@fakeemail.com | +1-555-0101 | San Francisco, CA

    SUMMARY
    Software Engineer with 5+ years of experience building scalable web
    applications using Python, JavaScript, and cloud technologies.

    SKILLS
    Python, JavaScript, TypeScript, React, Node.js, Django, Flask, FastAPI,
    PostgreSQL, MongoDB, Redis, Docker, Kubernetes, AWS, Git, CI/CD,
    REST, GraphQL, Agile, Scrum

    EXPERIENCE
    Senior Software Engineer — TechCorp Inc., San Francisco, CA
    Jan 2021 – Present
    - Designed and built microservices architecture serving 2M+ requests/day
    - Led migration from monolith to Kubernetes-based deployment
    - Mentored team of 4 junior developers

    Software Engineer — WebStart LLC, Austin, TX
    Jun 2018 – Dec 2020
    - Developed full-stack features using React and Django REST Framework
    - Implemented CI/CD pipelines with GitHub Actions
    - Reduced API response time by 40% through query optimization

    EDUCATION
    B.S. in Computer Science — University of Texas at Austin, 2018

    CERTIFICATIONS
    AWS Certified Solutions Architect – Associate
    Certified Kubernetes Administrator (CKA)
""")

RESUME_JANE_SMITH = textwrap.dedent("""\
    Jane Smith
    jane.smith@datamail.org | +1-555-0202 | New York, NY

    PROFILE
    Data Scientist with expertise in machine learning, NLP, and statistical
    modeling. Published researcher with 3+ years of industry experience.

    TECHNICAL SKILLS
    Python, R, SQL, TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy,
    Matplotlib, Seaborn, Jupyter Notebook, Apache Spark, Hadoop,
    AWS, Docker, Tableau, Power BI, NLP, Deep Learning, Machine Learning,
    Statistical Analysis, A/B Testing, Feature Engineering

    EXPERIENCE
    Data Scientist — DataViz Analytics, New York, NY        Jul 2021 – Present
    • Built NLP pipeline for sentiment analysis achieving 92% accuracy
    • Developed customer churn prediction model (XGBoost) reducing churn by 15%
    • Created interactive dashboards with Tableau for executive reporting

    ML Engineer Intern — AI Solutions Corp, Boston, MA     Jan 2020 – Jun 2021
    • Implemented recommendation system using collaborative filtering
    • Processed 50GB+ datasets using PySpark on AWS EMR
    • Published paper on transfer learning for medical imaging at ICML workshop

    EDUCATION
    M.S. in Data Science — Columbia University, 2021
    B.Tech in Computer Science — IIT Delhi, 2019

    AWARDS
    Best Paper Award, ICML Workshop on Healthcare ML, 2021
""")

RESUME_ALEX_KUMAR = textwrap.dedent("""\
    Alex Kumar
    alex.kumar@pmhub.net | +1-555-0303 | Seattle, WA

    OBJECTIVE
    Experienced Product Manager with a passion for building user-centric
    products. Skilled in agile methodologies, data-driven decision making,
    and cross-functional team leadership.

    SKILLS
    Product Management, Agile, Scrum, Kanban, Jira, Confluence,
    SQL, Python, Tableau, Figma, A/B Testing, User Research,
    Stakeholder Management, Strategic Planning, Communication,
    Leadership, Cross-functional, Data Visualization, Presentation Skills

    EXPERIENCE
    Senior Product Manager — CloudScale Inc., Seattle, WA
    Mar 2020 – Present
    - Managed product roadmap for SaaS platform with $50M ARR
    - Led cross-functional team of 12 (engineering, design, QA)
    - Increased user engagement by 35% through data-driven feature prioritization
    - Conducted 50+ user interviews to inform product strategy

    Product Manager — StartupHub, San Jose, CA
    Aug 2017 – Feb 2020
    - Launched 3 major product features from ideation to release
    - Defined and tracked KPIs using SQL and Tableau dashboards
    - Collaborated with engineering to reduce sprint cycle time by 20%

    EDUCATION
    MBA — Stanford Graduate School of Business, 2017
    B.S. in Information Technology — University of Washington, 2015

    CERTIFICATIONS
    Certified Scrum Master (CSM)
    PMI-ACP
""")

RESUME_MARIA_CHEN = textwrap.dedent("""\
    Maria Chen
    maria.chen@cloudops.io | +1-555-0404 | Denver, CO

    SUMMARY
    DevOps Engineer with 4 years of experience in CI/CD, infrastructure
    automation, and cloud platform management. Strong background in
    Linux, Docker, Kubernetes, and AWS.

    SKILLS
    Docker, Kubernetes, AWS, Azure, Terraform, Ansible, Jenkins,
    GitHub Actions, Linux, Bash, Python, Go, Nginx, Prometheus,
    Grafana, ELK Stack, Helm, ArgoCD, CI/CD, Git, Monitoring

    EXPERIENCE
    DevOps Engineer — InfraCloud Technologies, Denver, CO
    May 2021 – Present
    - Managed Kubernetes clusters (50+ nodes) across AWS and Azure
    - Built CI/CD pipelines with Jenkins and GitHub Actions
    - Implemented infrastructure as code using Terraform (200+ resources)
    - Set up monitoring stack with Prometheus, Grafana, and PagerDuty

    Junior DevOps Engineer — ServerFarm Inc., Portland, OR
    Jul 2019 – Apr 2021
    - Automated server provisioning with Ansible playbooks
    - Containerized 15+ microservices with Docker
    - Maintained 99.9% uptime for production infrastructure

    EDUCATION
    B.S. in Computer Engineering — Oregon State University, 2019
""")

RESUME_SAM_WILSON = textwrap.dedent("""\
    Sam Wilson
    sam.wilson@bizanalytics.com | +1-555-0505 | Chicago, IL

    PROFILE
    Business Analyst with 3+ years of experience in data analysis,
    requirements gathering, and process improvement.

    SKILLS
    SQL, Excel, Power BI, Tableau, Python, Pandas, Jira, Confluence,
    Stakeholder Management, Communication, Agile, Scrum,
    Data Visualization, Requirements Analysis, Process Improvement,
    Critical Thinking, Problem Solving, Presentation Skills

    EXPERIENCE
    Business Analyst — FinServ Group, Chicago, IL
    Jun 2021 – Present
    - Analyzed transaction data to identify fraud patterns, saving $2M/year
    - Created weekly Power BI dashboards for C-level executives
    - Facilitated requirements workshops with 10+ stakeholders
    - Wrote BRDs and functional specifications for 5 major projects

    Junior Analyst — ConsultCo, Chicago, IL
    Sep 2019 – May 2021
    - Performed data cleaning and exploratory analysis using SQL and Python
    - Supported PMO with Agile sprint planning and retrospectives
    - Conducted competitive analysis for 3 client engagements

    EDUCATION
    B.A. in Economics — University of Chicago, 2019

    CERTIFICATIONS
    Six Sigma Green Belt
    Certified Business Analysis Professional (CBAP)
""")

# ---------------------------------------------------------------------------
# Synthetic job descriptions
# ---------------------------------------------------------------------------

JD_SWE_FULLSTACK = textwrap.dedent("""\
    Full-Stack Developer

    Company: TechForward Solutions
    Location: Remote (US)

    About the Role:
    We are looking for a skilled Full-Stack Developer to join our engineering
    team. You will work on building and maintaining web applications that
    serve millions of users.

    Required Skills & Qualifications:
    - 3+ years of experience in full-stack web development
    - Strong proficiency in JavaScript, TypeScript, and React
    - Backend experience with Python (Django or FastAPI) or Node.js
    - Experience with PostgreSQL or MongoDB
    - Familiarity with Docker and CI/CD pipelines
    - Bachelor's degree in Computer Science or related field

    Nice to Have:
    - Experience with Kubernetes and AWS
    - Knowledge of GraphQL
    - Experience with Redis for caching
    - Contributions to open source projects

    Benefits:
    - Competitive salary + equity
    - Fully remote work environment
    - Health, dental, and vision insurance
    - Annual learning budget of $2,000
""")

JD_DATA_SCIENTIST = textwrap.dedent("""\
    Data Scientist

    Company: InsightAI Labs
    Location: New York, NY (Hybrid)

    About the Role:
    InsightAI Labs is seeking a Data Scientist to develop machine learning
    models that drive product decisions and improve customer experience.

    Required Qualifications:
    - Master's degree in Data Science, Statistics, Computer Science, or related field
    - 2+ years of experience in data science or machine learning roles
    - Strong programming skills in Python, with expertise in Pandas, Scikit-learn, and TensorFlow or PyTorch
    - Experience with SQL and data pipeline tools
    - Solid understanding of statistical analysis and A/B Testing
    - Excellent communication and presentation skills

    Preferred Qualifications:
    - Experience with NLP or Computer Vision
    - Familiarity with Apache Spark or Hadoop
    - Experience with cloud platforms (AWS, GCP, or Azure)
    - Published research or conference papers

    What We Offer:
    - Base salary: $130,000 – $170,000
    - Annual performance bonus
    - Flexible hybrid work schedule
""")

JD_DEVOPS = textwrap.dedent("""\
    DevOps Engineer

    Company: CloudNine Infrastructure
    Location: Denver, CO (On-site)

    About the Role:
    We need a DevOps Engineer to build and maintain our cloud infrastructure,
    CI/CD pipelines, and monitoring systems. You'll work closely with
    development teams to ensure reliable, scalable deployments.

    Must Have:
    - 3+ years of experience in DevOps or SRE roles
    - Expert-level knowledge of Docker and Kubernetes
    - Experience with AWS or Azure cloud platforms
    - Proficiency in infrastructure-as-code tools (Terraform or Ansible)
    - Strong Linux administration skills
    - Experience with CI/CD tools (Jenkins, GitHub Actions, or GitLab CI)
    - Scripting skills in Python or Bash

    Bonus Skills:
    - Experience with Helm and ArgoCD
    - Knowledge of Prometheus and Grafana for monitoring
    - Familiarity with service mesh technologies (Istio)
    - Certified Kubernetes Administrator (CKA) certification is a plus

    Requirements:
    - Bachelor's degree in Computer Science, Engineering, or equivalent experience
    - Strong problem solving and collaboration skills
""")


def create_samples():
    """Generate all synthetic sample files."""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "data", "samples")
    resume_dir = os.path.join(base_dir, "resumes")
    jd_dir = os.path.join(base_dir, "job_descriptions")
    os.makedirs(resume_dir, exist_ok=True)
    os.makedirs(jd_dir, exist_ok=True)

    # --- PDFs (using reportlab) ---
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch

        _create_clean_pdf(resume_dir, "john_doe_swe.pdf", RESUME_JOHN_DOE)
        _create_messy_pdf(resume_dir, "jane_smith_ds.pdf", RESUME_JANE_SMITH)
        _create_scanned_pdf(resume_dir, "sam_wilson_analyst.pdf", RESUME_SAM_WILSON)
        print("✓ Created PDF resumes")
    except ImportError:
        print("✗ reportlab not installed — skipping PDF generation. Run: pip install reportlab")

    # --- DOCX (using python-docx) ---
    try:
        from docx import Document
        from docx.shared import Pt

        _create_docx(resume_dir, "alex_kumar_pm.docx", RESUME_ALEX_KUMAR)
        print("✓ Created DOCX resume")
    except ImportError:
        print("✗ python-docx not installed — skipping DOCX generation. Run: pip install python-docx")

    # --- PNG image resume (using Pillow) ---
    try:
        from PIL import Image, ImageDraw, ImageFont

        _create_image_resume(resume_dir, "maria_chen_devops.png", RESUME_MARIA_CHEN)
        print("✓ Created PNG image resume")
    except ImportError:
        print("✗ Pillow not installed — skipping PNG generation. Run: pip install Pillow")

    # --- Job descriptions (plain text) ---
    for fname, content in [
        ("swe_fullstack.txt", JD_SWE_FULLSTACK),
        ("data_scientist.txt", JD_DATA_SCIENTIST),
        ("devops_engineer.txt", JD_DEVOPS),
    ]:
        with open(os.path.join(jd_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)
    print("✓ Created job description text files")

    print(f"\nAll samples created in: {os.path.abspath(base_dir)}")


def _create_clean_pdf(output_dir: str, filename: str, text: str):
    """Create a clean, well-formatted PDF resume."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch

    filepath = os.path.join(output_dir, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    story = []

    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 6))
            continue
        # Make section headers bold
        if line.isupper() and len(line) < 40:
            story.append(Paragraph(f"<b>{line}</b>", styles["Heading2"]))
        else:
            story.append(Paragraph(line, styles["Normal"]))

    doc.build(story)


def _create_messy_pdf(output_dir: str, filename: str, text: str):
    """Create a messy multi-column style PDF (to test parser robustness)."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors

    filepath = os.path.join(output_dir, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            topMargin=0.3*inch, bottomMargin=0.3*inch,
                            leftMargin=0.3*inch, rightMargin=0.3*inch)
    styles = getSampleStyleSheet()
    story = []

    lines = text.strip().split("\n")
    # Put first few lines as header
    for line in lines[:3]:
        line = line.strip()
        if line:
            story.append(Paragraph(line, styles["Heading1"] if lines.index(line + "\n") == 0
                                   if False else styles["Normal"]))

    # Split remaining into two columns using a table
    mid = len(lines) // 2
    left_col = "\n".join(lines[3:mid])
    right_col = "\n".join(lines[mid:])

    left_paras = [Paragraph(l.strip(), styles["Normal"]) for l in left_col.split("\n") if l.strip()]
    right_paras = [Paragraph(l.strip(), styles["Normal"]) for l in right_col.split("\n") if l.strip()]

    # Pad shorter column
    max_len = max(len(left_paras), len(right_paras))
    left_paras.extend([Paragraph("", styles["Normal"])] * (max_len - len(left_paras)))
    right_paras.extend([Paragraph("", styles["Normal"])] * (max_len - len(right_paras)))

    table_data = list(zip(left_paras, right_paras))
    table = Table(table_data, colWidths=[3.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.grey),
    ]))
    story.append(table)

    doc.build(story)


def _create_scanned_pdf(output_dir: str, filename: str, text: str):
    """Create a PDF that contains text as an image (simulating a scanned document)."""
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, ReportLabImage
    from reportlab.lib.units import inch
    import tempfile

    # First create an image of the text
    img_width, img_height = 2550, 3300  # 300 DPI letter size
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    # Use default font (no external font dependency)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except (OSError, IOError):
        font = ImageFont.load_default()

    y_offset = 100
    for line in text.strip().split("\n"):
        line = line.strip()
        if y_offset > img_height - 100:
            break
        draw.text((100, y_offset), line, fill="black", font=font)
        y_offset += 35

    # Save as temp image, then embed in PDF
    temp_img = os.path.join(output_dir, f"_temp_{filename}.png")
    img.save(temp_img)

    filepath = os.path.join(output_dir, filename)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    story = [ReportLabImage(temp_img, width=7.5*inch, height=10*inch)]
    doc.build(story)

    os.remove(temp_img)


def _create_docx(output_dir: str, filename: str, text: str):
    """Create a DOCX resume."""
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line:
            doc.add_paragraph("")
            continue
        if line.isupper() and len(line) < 40:
            p = doc.add_heading(line, level=2)
        elif text.strip().split("\n")[0].strip() == line:
            p = doc.add_heading(line, level=1)
        else:
            p = doc.add_paragraph(line)

    filepath = os.path.join(output_dir, filename)
    doc.save(filepath)


def _create_image_resume(output_dir: str, filename: str, text: str):
    """Create a PNG image of a resume (simulating a scanned document)."""
    from PIL import Image, ImageDraw, ImageFont

    img_width, img_height = 2550, 3300
    img = Image.new("RGB", (img_width, img_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except (OSError, IOError):
        font = ImageFont.load_default()

    y_offset = 100
    for line in text.strip().split("\n"):
        line = line.strip()
        if y_offset > img_height - 100:
            break
        draw.text((100, y_offset), line, fill="black", font=font)
        y_offset += 40

    filepath = os.path.join(output_dir, filename)
    img.save(filepath)


if __name__ == "__main__":
    create_samples()
