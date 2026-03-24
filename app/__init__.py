from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

def _ensure_column_exists(table, column, column_sql):
    inspector = inspect(db.engine)
    if table not in inspector.get_table_names():
        return

    column_names = {col["name"] for col in inspector.get_columns(table)}
    if column in column_names:
        return

    with db.engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {column_sql}"))

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "supersecretkey"

    # Database
    app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:osama4545@localhost/flask_apis"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    # MAIL CONFIG
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = "seth73602@gmail.com"
    app.config["MAIL_PASSWORD"] = "ayht idek ajkv rfgl"
    app.config["MAIL_DEFAULT_SENDER"] = "seth73602@gmail.com"
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_ECHO'] = True
    db.init_app(app)
    mail.init_app(app)

    # Ensure model metadata is loaded before create_all()
    from . import models  # noqa: F401

    with app.app_context():
        db.create_all()
        try:
            _ensure_column_exists("product", "image", "image VARCHAR(200)")
            _ensure_column_exists("product", "category_id", "category_id INTEGER")
        except Exception as e:
            print(f"Schema sync warning: {e}")
        print("Database table created")

    # Register Blueprints
    from .api.routes import api_bp
    from .auth.routes import api_auth
    from .main.routes import main
    
    app.register_blueprint(api_bp)
    app.register_blueprint(api_auth)
    app.register_blueprint(main)

    @app.context_processor
    def inject_user():
        from .models import User
        from flask import session

        user = None
        if "user_id" in session:
            user = User.query.get(session["user_id"])
        return dict(current_user=user)

    return app