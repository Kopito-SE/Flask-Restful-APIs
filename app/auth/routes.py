from flask import Blueprint, request, redirect, url_for, jsonify, current_app 
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
import random
from flask_mail import Message
import jwt
from datetime import datetime, timedelta
from functools import wraps
from ..models import User
from .. import db, mail  # Added mail import

# Api Blueprint
api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

# OAuth Setup
oauth = OAuth()

# Google OAuth registration
def init_google_oauth(app):
    oauth.init_app(app)
    
    # Store the google client in oauth object
    oauth.register(
        name="google",
        client_id=app.config.get("GOOGLE_CLIENT_ID"),
        client_secret=app.config.get("GOOGLE_CLIENT_SECRET"),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',  # Use this instead of individual URLs
        client_kwargs={"scope": "openid email profile"}
    )

# Token Required Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization","").replace("Bearer ", "")

        if not token:
            return jsonify({"error":"Token is missing"}), 401
        try:
            data = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user = User.query.get(data["user_id"])
            if not user:
                return jsonify({"error":"User not found"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"error":"Token expired"}),401
        except jwt.InvalidTokenError:
            return jsonify({"error":"Invalid token"}),401
        return f(user, *args, **kwargs)
    return decorated
        

@api_auth.route("/register", methods=["POST"])
def register():

     # Get Json data
    data = request.get_json() or {}
    required = ["email", "username", "password"]

     # Check the required fields
    if not all(data.get(field) for field in required):
        return jsonify({"error":"Missing required fields","required":required}),400
    email, username, password = data["email"], data["username"], data["password"]

     # Validate password
    if len(password)  < 6:
        return jsonify({"error":"Password must be atleast 6 characters"}),404

     # Check existing User
    if User.query.filter_by(username=username).first():
        return jsonify({"error":"Username already Exist"}),409
    if User.query.filter_by(email=email).first():
        return jsonify({"error":"Email already registered"}),409

     # Create user
    code = str(random.randint(100000, 999999))
    user = User(
        email=email,
        username=username,
        password=generate_password_hash(password),
        verified=False,
        verification_code=code,
        code_expiry=datetime.utcnow() + timedelta(minutes=5),
        auth_provider='email',  # ← Explicitly set
        google_id=None
    )

    db.session.add(user)
    db.session.commit()

    # Send email
    try:
        msg = Message("Verification Code", recipients=[email])
        msg.body = f"Your Verification code is : {code}\n Expires in 5 min."
        mail.send(msg)

        return jsonify({
            "message": "Registration Successful.Please Verify your email.",
            "user_id": user.id,
            "email": email
        }), 201
    except Exception as e:
        # If email fails, delete the user
        db.session.delete(user)
        db.session.commit()
        return jsonify({"error":f"Failed to send verification email: {str(e)}"})


@api_auth.route("/verify-email", methods=["POST"]) 
def verify_email():
    """Verify user email with code"""

    data = request.get_json()
    if not data or not data.get("email") or not data.get("code"):
        return jsonify({"error":"Email and verification code required"}),400
    
    email = data.get("email")
    code = data.get("code")

    # Find unverified user
    user = User.query.filter_by(email=email, verified=False).first()

    if not user:
        return jsonify({"error":"User not found or already verified"}),404
    
    # Check if code matches and not expired
    if user.verification_code == code and user.code_expiry > datetime.utcnow():
        user.verified = True
        user.verification_code = None
        user.code_expiry = None
        db.session.commit()

        return jsonify({
            "message":"Email verification successful.You can now login."
        }),200
    else:
        return jsonify({"error":"Invalid or expired code"}),400
    

@api_auth.route("/resend-code",methods=["POST"])
def resend_code():
    """Resend verification code"""

    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({"error":"Email required"})
    
    email = data.get("email")
    user = User.query.filter_by(email=email, verified = False).first()

    if not user:
        return jsonify({"error":"User not found or already verified"}),404

    # Generate new code
    code = random.randint(100000,999999)
    user.verification_code = str(code)
    user.code_expiry = datetime.utcnow() + timedelta(minutes=5)

    db.session.commit()

    # Send email
    msg = Message(
        'New Verification Code',
        recipients=[email]
    )

    msg.body = f"Your new verification code is {code}\n This code expires in 5 min."

    mail.send(msg)

    return jsonify({"message":"New Verification Code Sent"}),200


@api_auth.route("/login", methods = ["POST"])
def login():
    """Login user and return JWT token"""

    data = request.get_json()

    if not data:
        return jsonify({"error":"No Data provided"}),400
    
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error":"Username and Password required"}),400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({"error":"Invalid Credentials"}),401
    # Check if user registered via Google
    if user.password is None:
        return jsonify({"error":"This account uses Google Login. Please use Google Sign In"}),400

    if not check_password_hash(user.password, password):
        return jsonify({"error":"Invalid Credentials"}),401

    if not user.verified:
        return jsonify({"error":"Please Verify your email first"}),403

    # Generate JWT tOKENS
    token = jwt.encode({
        'user_id':user.id,
        'username':user.username,
        'exp':datetime.utcnow() + timedelta(hours=24)
    }, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        "message":"Login Successful",
        "token": token,
        "user":{
            "id": user.id,
            "username":user.username,
            "email": user.email
        }
    }),200


# ---------------- GOOGLE LOGIN ---------------- #

@api_auth.route("/login/google")
def google_login():
    redirect_uri = url_for("api_auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@api_auth.route("/login/google/callback")
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        resp = oauth.google.get("https://www.googleapis.com/oauth2/v3/userinfo")
        user_info = resp.json()

        email = user_info["email"]
        google_id = user_info["sub"]  # 'sub' is Google's unique identifier
        username = user_info.get("name", email.split("@")[0])

        user = User.query.filter_by(google_id=google_id).first()

        if not user:
            user = User.query.filter_by(email=email).first()
            
            if user:
                user.auth_provider = 'both'
                user.google_id = google_id

                db.session.commit()
            else:
                # Brand new user - create with Google
                user = User(
                    email=email,
                    username=username,
                    password=None,  # No password since it's Google auth
                    verified=True,
                    auth_provider='google',
                    google_id=google_id
                )
            db.session.add(user)
            db.session.commit()

        jwt_token = jwt.encode({
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, current_app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({
            "message": "Google Login Successful",
            "token": jwt_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "auth_provider": user.auth_provider
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@api_auth.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    """Logout user (client-side: discard token)"""
    return jsonify({
        "message":"Logged out Successfully"
    }), 200


@api_auth.route("/profile", methods=["GET"])  
@token_required 
def get_profile(current_user):
    """Get current user profile"""

    return jsonify({
        "user":{
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "verified": current_user.verified,
            "created_at": str(current_user.created_at) if current_user.created_at else None
        }
    }),200


@api_auth.route("/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    """Update user profile"""

    data = request.get_json()

    if data.get("username"):
         # Check if username is taken
        existing = User.query.filter_by(username = data["username"]).first()

        if existing and existing.id != current_user.id:
            return jsonify({"error":"Username already taken"}),409

        current_user.username = data["username"]
    
    if data.get("email"):
        # Check if email is taken
        existing = User.query.filter_by(email=data["email"]).first()

        if existing and existing.id != current_user.id:
            return jsonify({"error": "Email already registered"}), 409

        current_user.email = data["email"]
        current_user.verified = False
    
    db.session.commit()

    return jsonify({
        "message":"Profile Updated Successfully",
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "verified": current_user.verified
        }
    }),200


@api_auth.route("/change-password",methods=["POST"])
@token_required
def change_password(current_user):
    """Change user password"""

    data = request.get_json()

    if not data or not data.get("current_password") or not data.get("new_password"):
        return jsonify({"error": "Current password and new password required"}), 400
    
    if not check_password_hash(current_user.password, data["current_password"]):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    if len(data["new_password"]) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    
    current_user.password = generate_password_hash(data["new_password"])

    db.session.commit()
    
    return jsonify({"message": "Password changed successfully"}), 200


@api_auth.route("/request-reset-password", methods=["POST"])
def request_password_reset():
    """Send password reset code to email"""

    data = request.get_json()

    if not data or not data.get("email"):
        return jsonify({"error":"Email is required"}),400

    email = data.get("email")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error":"User not found"}),404

     # Generate reset code
    code = str(random.randint(100000,999999))

    user.verification_code = code
    user.code_expiry = datetime.utcnow() + timedelta(minutes=5)

    db.session.commit()

    #Send email
    try:
        msg = Message(
            "Password Reset Code",
            recipients =[email]
        )

        msg.body = f"Your Password Reset code is {code}\nExpires in 5 min"

        mail.send(msg)

        return jsonify({"message":"Password reset code sent to you email"}), 200

    except Exception as e:
        return jsonify({"error":f"Failed to send reset email: {str(e)}"}),500
    

@api_auth.route("/reset-password", methods = ["POST"])
def reset_password():

    data = request.get_json()

    required = ("email","code","new_password")

    if not all(data.get(field) for field in required):
        return jsonify({"error":"Email,Code and New_Password required"}), 400
    
    email = data.get("email")
    code = data.get("code")
    new_password = data.get("new_password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error":"User not found"}),404

     # Check code
    if user.verification_code != code:
        return jsonify({"error":"Invalid Code"}),400

    # Check expiry
    if not user.code_expiry or datetime.utcnow() > user.code_expiry:
        return jsonify({"error":"Code expired"}), 400

    # Validate password
    if len(new_password) < 6 :
        return jsonify({"error":"Password Must be more than 6 characters"}), 400

    # Update password
    user.password = generate_password_hash(new_password)

    # Clear reset code
    user.verification_code = None
    user.code_expiry = None

    db.session.commit()
    
    return jsonify({"message":"Password reset successfully"}),200