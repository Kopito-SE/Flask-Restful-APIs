from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, current_app 
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from .. import db
import random
from flask_mail import Message
from .. import mail
import jwt
from datetime import datetime, timedelta
from functools import wraps

# Api Blueprint
api_auth = Blueprint("api_auth", __name__, url_prefix="/api/auth")

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
        code_expiry=datetime.utcnow() + timedelta(minutes=5)
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
    except:
         # If email fails, delete the user
        db.session.delete(user)
        db.session.commit()
        return jsonify({"error":"Failed to send verification email"})

    

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
            "message":"Email verification successfull.You can now login."
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
        return jsonify({"error":"No Data provied"}),400
    
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error":"Username and Password required"}),400
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"error":"Invalid Credentials"}),401
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
        "message":"Login Successfull",
        "token": token,
        "user":{
            "id": user.id,
            "username":user.username,
            "email": user.email
        }
    }),200
@api_auth.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    """Logout user (client-side: discard token)"""
     # Since JWTs are stateless, we just return success
     # Client should delete the token
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
            "created_at":current_user.created_at
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
        current_user.verified = False  # Require re-verification
    
    db.session.commit()

    return jsonify({
        "message":"Profile Updated Successfullly",
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






    
    
    
   
    



