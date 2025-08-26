from functools import wraps
from flask import request, jsonify
import jwt
from .models import User
from flask import current_app as app


def token_required(f):
    """
    Decorator to check if a valid JWT token is in the request headers. If not, returns a 401 error.
    If the token is valid, passes the current user as the first argument to the decorated function.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        """
        Decorator to check if a valid JWT token is in the request headers. If not, returns a 401 error.
        If the token is valid, passes the current user as the first argument to the decorated function.
        """
        token = None
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            current_user = User.query.get(data["user_id"])
        except:
            return jsonify({"message": "Token is invalid!"}), 401
        return f(current_user, *args, **kwargs)

    return decorated


def admin_required(f):
    """
    Decorator that checks if a user has the Admin role before allowing access to
    a route. If not, returns a 403 error.
    """

    @wraps(f)
    @token_required
    def decorated(current_user, *args, **kwargs):
        if current_user.role != "Admin":
            return jsonify({"message": "Admin role required!"}), 403
        return f(current_user, *args, **kwargs)

    return decorated
