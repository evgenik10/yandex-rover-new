from flask import Flask, redirect, render_template, request, session, url_for
from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash

from api import api
from models import Rover, User, db


def _safe_alter(app, sql: str):
    with app.app_context():
        try:
            db.session.execute(text(sql))
            db.session.commit()
        except Exception:
            db.session.rollback()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fleet.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()

    _safe_alter(app, "ALTER TABLE rover ADD COLUMN ip_address VARCHAR(64) DEFAULT '0.0.0.0'")
    _safe_alter(app, "ALTER TABLE rover ADD COLUMN last_lat FLOAT")
    _safe_alter(app, "ALTER TABLE rover ADD COLUMN last_lon FLOAT")

    with app.app_context():
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password_hash=generate_password_hash("admin123"), role="admin"))
        if not Rover.query.filter_by(id="rover-001").first():
            db.session.add(Rover(id="rover-001", name="Pilot Rover", ip_address="192.168.1.50", api_token="CHANGE_ME"))
        db.session.commit()

    @app.route("/")
    def index():
        if "uid" not in session:
            return redirect(url_for("login"))
        return render_template("dashboard.html", user_role=session.get("role", "viewer"), username=session.get("username", "unknown"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            u = User.query.filter_by(username=request.form["username"]).first()
            if u and check_password_hash(u.password_hash, request.form["password"]):
                session["uid"] = u.id
                session["role"] = u.role
                session["username"] = u.username
                return redirect(url_for("index"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=True)
