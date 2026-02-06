from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from api import api
from models import Rover, User, db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-change-me"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///fleet.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.register_blueprint(api)

    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            db.session.add(User(username="admin", password_hash=generate_password_hash("admin123"), role="admin"))
        if not Rover.query.filter_by(id="rover-001").first():
            db.session.add(Rover(id="rover-001", name="Pilot Rover", api_token="CHANGE_ME"))
        db.session.commit()

    @app.route("/")
    def index():
        if "uid" not in session:
            return redirect(url_for("login"))
        return render_template("dashboard.html", user_role=session.get("role", "viewer"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            u = User.query.filter_by(username=request.form["username"]).first()
            if u and check_password_hash(u.password_hash, request.form["password"]):
                session["uid"] = u.id
                session["role"] = u.role
                return redirect(url_for("index"))
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=8000, debug=True)
