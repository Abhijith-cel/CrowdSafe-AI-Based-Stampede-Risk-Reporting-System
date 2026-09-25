"""Authentication and user management routes."""

import logging
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from ..database import db
from ..models import User

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user (citizen or authority)."""
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "citizen").strip().lower()
    phone = data.get("phone", "").strip()

    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400

    if role not in ("citizen", "authority", "admin"):
        role = "citizen"

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return jsonify({"error": "Username or email already in use"}), 409

    user = User(username=username, email=email, role=role, phone=phone)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "User registered successfully",
        "access_token": token,
        "user": user.to_dict(),
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate a user and return a JWT access token."""
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip()
    password = data.get("password", "")

    if not identifier or not password:
        return jsonify({"error": "Identifier (username/email) and password are required"}), 400

    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({
        "message": "Login successful",
        "access_token": token,
        "user": user.to_dict(),
    }), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_current_user():
    """Retrieve profile of the authenticated user."""
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"user": user.to_dict()}), 200
