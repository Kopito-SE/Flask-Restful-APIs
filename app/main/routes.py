from flask import Blueprint, render_template

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("login.html")

@main.route("/login")
def login():
    return render_template("login.html")

@main.route("/register")
def register():
    return render_template("register.html")



@main.route("/verify")
def verify():
    return render_template("verify.html")

@main.route("/reset-request")
def reset_request():
    return render_template("reset_request.html")

@main.route("/reset-password")
def reset_password():
    return render_template("reset_password.html")

@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
@main.route("/profile")
def profile():
    return render_template("profile.html")

@main.route("/settings")
def settings():
    return render_template("settings.html")