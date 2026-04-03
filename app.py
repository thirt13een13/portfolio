import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
# Railway injects DATABASE_URL automatically; fallback to SQLite for local dev
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///portfolio.db")

# SQLAlchemy requires postgresql:// not postgres:// (Railway may return old format)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

db = SQLAlchemy(app)


# ─── Models ───────────────────────────────────────────────────────────────────

class Project(db.Model):
    __tablename__ = "projects"
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    tech_stack  = db.Column(db.String(250))
    github_url  = db.Column(db.String(300))
    live_url    = db.Column(db.String(300))
    category    = db.Column(db.String(60), default="Web")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tech_stack": self.tech_stack,
            "github_url": self.github_url,
            "live_url": self.live_url,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
        }


class Message(db.Model):
    __tablename__ = "messages"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(200), nullable=False)
    subject    = db.Column(db.String(200))
    body       = db.Column(db.Text, nullable=False)
    is_read    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Seed data helper ─────────────────────────────────────────────────────────

def seed_projects():
    if Project.query.count() == 0:
        samples = [
            Project(
                title="E-Commerce Platform",
                description="Full-stack online store with cart, payments via Stripe, and admin dashboard. Handles 10k+ SKUs with real-time inventory tracking.",
                tech_stack="Python, Flask, PostgreSQL, Redis, Stripe API",
                github_url="https://github.com",
                live_url="https://example.com",
                category="Full-Stack",
            ),
            Project(
                title="AI Resume Screener",
                description="NLP-powered tool that ranks resumes against job descriptions using transformer embeddings. Reduced screening time by 70%.",
                tech_stack="Python, FastAPI, HuggingFace, React, Docker",
                github_url="https://github.com",
                live_url="https://example.com",
                category="AI/ML",
            ),
            Project(
                title="Real-Time Dashboard",
                description="WebSocket-driven analytics dashboard with live charts, anomaly alerts, and CSV export. Supports 500 concurrent users.",
                tech_stack="Node.js, Socket.IO, Chart.js, PostgreSQL",
                github_url="https://github.com",
                live_url="https://example.com",
                category="Data",
            ),
            Project(
                title="Mobile Fitness App",
                description="Cross-platform workout tracker with AI-generated plans, progress photos, and social sharing. 4.8★ on both stores.",
                tech_stack="React Native, Expo, Firebase, TensorFlow Lite",
                github_url="https://github.com",
                live_url="https://example.com",
                category="Mobile",
            ),
        ]
        db.session.add_all(samples)
        db.session.commit()


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    projects = Project.query.order_by(Project.created_at.desc()).limit(3).all()
    return render_template("index.html", projects=projects)


@app.route("/projects")
def projects():
    category = request.args.get("category", "All")
    if category == "All":
        all_projects = Project.query.order_by(Project.created_at.desc()).all()
    else:
        all_projects = Project.query.filter_by(category=category).order_by(Project.created_at.desc()).all()
    categories = ["All"] + sorted({p.category for p in Project.query.all()})
    return render_template("projects.html", projects=all_projects, categories=categories, active=category)


@app.route("/projects/new", methods=["GET", "POST"])
def new_project():
    if request.method == "POST":
        p = Project(
            title=request.form["title"],
            description=request.form["description"],
            tech_stack=request.form.get("tech_stack", ""),
            github_url=request.form.get("github_url", ""),
            live_url=request.form.get("live_url", ""),
            category=request.form.get("category", "Web"),
        )
        db.session.add(p)
        db.session.commit()
        flash("Project added successfully!", "success")
        return redirect(url_for("projects"))
    return render_template("project_form.html", project=None, action="Create")


@app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
def edit_project(project_id):
    p = Project.query.get_or_404(project_id)
    if request.method == "POST":
        p.title       = request.form["title"]
        p.description = request.form["description"]
        p.tech_stack  = request.form.get("tech_stack", "")
        p.github_url  = request.form.get("github_url", "")
        p.live_url    = request.form.get("live_url", "")
        p.category    = request.form.get("category", "Web")
        p.updated_at  = datetime.utcnow()
        db.session.commit()
        flash("Project updated!", "success")
        return redirect(url_for("projects"))
    return render_template("project_form.html", project=p, action="Update")


@app.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    p = Project.query.get_or_404(project_id)
    db.session.delete(p)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("projects"))


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        msg = Message(
            name=request.form["name"],
            email=request.form["email"],
            subject=request.form.get("subject", ""),
            body=request.form["body"],
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent! I'll get back to you soon.", "success")
        return redirect(url_for("contact"))
    return render_template("contact.html")


# ─── JSON API (bonus REST endpoints) ──────────────────────────────────────────

@app.route("/api/projects")
def api_projects():
    return jsonify([p.to_dict() for p in Project.query.all()])


@app.route("/api/projects/<int:project_id>")
def api_project(project_id):
    return jsonify(Project.query.get_or_404(project_id).to_dict())


@app.route("/health")
def health():
    return jsonify({"status": "ok", "db": "connected"})


# ─── App init ─────────────────────────────────────────────────────────────────

with app.app_context():
    db.create_all()
    seed_projects()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")
