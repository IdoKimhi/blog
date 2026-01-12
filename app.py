import os
import sqlite3
from flask import Flask, g, redirect, render_template, request, session, url_for

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
DATABASE = os.getenv("DATABASE_URL", "blog.db")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
BASE_URL = os.getenv("BASE_URL", "").rstrip("/")


def ensure_database_path():
    directory = os.path.dirname(DATABASE)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_db():
    if "db" not in g:
        ensure_database_path()
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def is_admin():
    return session.get("is_admin", False)


@app.context_processor
def inject_base_url():
    return {"base_url": BASE_URL}


def init_db():
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            image_url TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            count INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    db.execute("INSERT OR IGNORE INTO visits (id, count) VALUES (1, 0)")
    columns = [row["name"] for row in db.execute("PRAGMA table_info(posts)").fetchall()]
    if "image_url" not in columns:
        db.execute("ALTER TABLE posts ADD COLUMN image_url TEXT")
    db.commit()


def increment_visit_count():
    db = get_db()
    db.execute("UPDATE visits SET count = count + 1 WHERE id = 1")
    db.commit()
    return db.execute("SELECT count FROM visits WHERE id = 1").fetchone()["count"]


@app.before_request
def before_request():
    init_db()


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    return redirect(url_for("feed"))


@app.route("/feed")
@app.route("/home")
def feed():
    db = get_db()
    visit_count = increment_visit_count()
    posts = db.execute(
        "SELECT id, title, image_url, content, created_at FROM posts ORDER BY created_at DESC"
    ).fetchall()
    return render_template("index.html", posts=posts, visit_count=visit_count)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    db = get_db()
    post = db.execute(
        "SELECT id, title, image_url, content, created_at FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()
    if post is None:
        return redirect(url_for("index"))
    return render_template("post.html", post=post)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not is_admin():
        return redirect(url_for("admin_login"))
    db = get_db()
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        image_url = request.form.get("image_url", "").strip() or None
        content = request.form.get("content", "").strip()
        if title and content:
            db.execute(
                "INSERT INTO posts (title, image_url, content) VALUES (?, ?, ?)",
                (title, image_url, content),
            )
            db.commit()
        return redirect(url_for("admin"))

    posts = db.execute(
        "SELECT id, title, image_url, created_at FROM posts ORDER BY created_at DESC"
    ).fetchall()
    return render_template("admin.html", posts=posts)


@app.route("/admin/edit/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    db = get_db()
    post = db.execute(
        "SELECT id, title, image_url, content FROM posts WHERE id = ?",
        (post_id,),
    ).fetchone()
    if post is None:
        return redirect(url_for("admin"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        image_url = request.form.get("image_url", "").strip() or None
        content = request.form.get("content", "").strip()
        if title and content:
            db.execute(
                "UPDATE posts SET title = ?, image_url = ?, content = ? WHERE id = ?",
                (title, image_url, content, post_id),
            )
            db.commit()
        return redirect(url_for("admin"))
    return render_template("admin_edit.html", post=post)


@app.route("/admin/delete/<int:post_id>", methods=["POST"])
def delete_post(post_id):
    if not is_admin():
        return redirect(url_for("admin_login"))
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
    return redirect(url_for("admin"))


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        token = request.form.get("token", "")
        if ADMIN_TOKEN and token == ADMIN_TOKEN:
            session["is_admin"] = True
            return redirect(url_for("admin"))
        error = "Invalid admin token."
    return render_template("admin_login.html", error=error, token_set=bool(ADMIN_TOKEN))


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("feed"))


@app.route("/maintenance")
@app.route("/maintance")
def maintenance():
    return render_template("maintenance.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "1000"))
    app.run(host="0.0.0.0", port=port, debug=False)
