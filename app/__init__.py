from flask import Flask, app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from flask_mail import Mail
from dotenv import load_dotenv
import os



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

def _add_oauth_columns():
    """Add OAuth columns to User table if they don't exist"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('user')]
        
        with db.engine.begin() as conn:
            if 'auth_provider' not in columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN auth_provider VARCHAR(20) DEFAULT 'email'"))
                print("Added auth_provider column")
            
            if 'google_id' not in columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN google_id VARCHAR(100) UNIQUE"))
                print("Added google_id column")
                
            # Change password to nullable
            if 'password' in columns:
                conn.execute(text("ALTER TABLE user MODIFY COLUMN password VARCHAR(200) NULL"))
                print("Modified password column to allow NULL")
                
    except Exception as e:
        print(f"Migration warning: {e}")


def _add_user_stats_columns():
    """Add user stats columns if they don't exist."""
    try:
        inspector = inspect(db.engine)
        columns = [col["name"] for col in inspector.get_columns("user")]

        with db.engine.begin() as conn:
            if "login_count" not in columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0"))
                print("Added login_count column")

            if "last_login" not in columns:
                conn.execute(text("ALTER TABLE user ADD COLUMN last_login DATETIME NULL"))
                print("Added last_login column")
    except Exception as e:
        print(f"Stats migration warning: {e}")

def create_app():
   
    app = Flask(__name__)

   

    load_dotenv()

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
    if not app.config["SECRET_KEY"]:
        raise ValueError("SECRET_KEY not found in .env file")
    # Database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["SQLALCHEMY_DATABASE_URI"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # MAIL CONFIG
    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True
    app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
    sender_name = os.environ.get("MAIL_SENDER_NAME")
    sender_email = os.environ.get("MAIL_SENDER_MAIL")
    app.config["MAIL_DEFAULT_SENDER"] = f'"{sender_name}" <{sender_email}>'
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_ECHO'] = True

    # GOOGLE OAUTH CONFIG
    app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Initialize extensions with app
    db.init_app(app)
    mail.init_app(app)

    # Initialize Google OAuth - ADD THIS LINE
    from .auth.routes import init_google_oauth
    init_google_oauth(app)

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
        
        # Add OAuth columns to User table
        _add_oauth_columns()
        _add_user_stats_columns()

    # Register Blueprints
    
    from .auth.routes import api_auth
    from .main.routes import main
    
    
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
