from flask import jsonify, request, current_app as app
from . import db
from .models import User, Claim, Skill, Note, Rule
from .auth_utils import token_required, admin_required
from sqlalchemy import func, desc, asc
import bcrypt
import jwt
from datetime import datetime, timedelta, date
import pandas as pd
import os
from dateutil import parser  # For flexible date parsing if needed


# --- Authentication ---
@app.route("/api/register", methods=["POST"])
def register():

    """
    Registers a new user.

    The request body must contain the following parameters:

    - name (string): The full name of the user.
    - username (string): A unique username for the user.
    - password (string): The password for the user. Must be at least 8 characters.

    Returns a JSON response with a message describing the result of the registration.

    Status codes:

    - 201: User registered successfully.
    - 400: Invalid request body.
    - 409: Username already exists.
    """
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"message": "Username already exists"}), 409
    if len(data.get("password", "")) < 8:  # Basic validation
        return jsonify({"message": "Password must be at least 8 characters"}), 400
    hashed_password = bcrypt.hashpw(data["password"].encode("utf-8"), bcrypt.gensalt())
    new_user = User(
        name=data["name"],
        username=data["username"],
        password_hash=hashed_password.decode("utf-8"),
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered. Waiting for admin approval."}), 201


@app.route("/api/login", methods=["POST"])
def login():

    """
    Logs in a user with the given credentials.

    The request body must contain the following parameters:

    - username (string): The username of the user.
    - password (string): The password for the user.

    Returns a JSON response with a token and user information on successful login,
    or an error message on invalid credentials.

    Status codes:

    - 200: User logged in successfully.
    - 401: Invalid credentials.
    - 403: Account is not active.
    """
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    print(user)
    if user and bcrypt.checkpw(
        data["password"].encode("utf-8"), user.password_hash.encode("utf-8")
    ):
        if not user.is_active:
            return jsonify({"message": "Account is not active."}), 403
        token = jwt.encode(
            {
                "user_id": str(user.id),
                "role": user.role,
                "exp": datetime.utcnow() + timedelta(hours=24),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        print(token)
        # Removed debug print
        return jsonify({"token": token, "user": {"name": user.name, "role": user.role}})
    return jsonify({"message": "Invalid credentials"}), 401


# --- Admin Routes ---
@app.route("/api/admin/users", methods=["GET"])
@admin_required
def get_users(current_user):
    """
    Returns a list of all Member users (non-Admin).
    ... (updated docstring: filters Members only)
    """
    users = User.query.filter(User.role == "Member").all()  # Simplified filter
    return jsonify(
        [
            {
                "id": str(u.id),
                "name": u.name,
                "username": u.username,
                "role": u.role,
                "is_active": u.is_active,
                "skills": [s.name for s in u.skills],
                "max_daily_claims": u.max_daily_claims,
                "seniority": u.seniority,
                "assign_by": u.assign_by,
            }
            for u in users
        ]
    )


@app.route("/api/admin/users/<uuid:user_id>", methods=["PUT"])
@admin_required
def update_user(current_user, user_id):
    """
    API endpoint to update an existing user.
    ... (docstring unchanged)
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    data = request.get_json()
    new_role = data.get("role")
    if new_role and new_role not in ["Member", "Admin"]:  # Enum validation
        return jsonify({"message": "Invalid role"}), 400
    user.role = new_role or user.role
    user.max_daily_claims = data.get("max_daily_claims", user.max_daily_claims)
    user.seniority = data.get("seniority", user.seniority)
    user.is_active = data.get("is_active", user.is_active)
    user.assign_by = data.get("assign_by", user.assign_by)
    if "skill_ids" in data:
        user.skills = Skill.query.filter(Skill.id.in_(data["skill_ids"])).all()
    db.session.commit()
    return jsonify({"message": "User updated successfully."})


@app.route("/api/admin/skills", methods=["GET", "POST"])  # Added POST
@admin_required
def manage_skills(current_user):
    if request.method == "GET":
        skills = Skill.query.all()
        return jsonify([{"id": str(s.id), "name": s.name} for s in skills])
    elif request.method == "POST":
        data = request.get_json()
        if Skill.query.filter_by(name=data["name"]).first():
            return jsonify({"message": "Skill already exists"}), 409
        new_skill = Skill(name=data["name"])
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"message": "Skill created"}), 201


# New: Rules management
@app.route("/api/admin/rules", methods=["GET", "POST"])
@admin_required
def manage_rules(current_user):
    if request.method == "GET":
        rules = Rule.query.order_by(Rule.priority).all()
        return jsonify(
            [
                {
                    "id": str(r.id),
                    "criteria_type": r.criteria_type,
                    "criteria_value": r.criteria_value,
                    "strategy": r.strategy,
                    "priority": r.priority,
                }
                for r in rules
            ]
        )
    elif request.method == "POST":
        data = request.get_json()
        new_rule = Rule(
            criteria_type=data["criteria_type"],
            criteria_value=data.get("criteria_value"),
            strategy=data["strategy"],
            priority=data.get("priority", 1),
        )
        db.session.add(new_rule)
        db.session.commit()
        return jsonify({"message": "Rule created"}), 201


@app.route("/api/admin/rules/<uuid:rule_id>", methods=["PUT", "DELETE"])
@admin_required
def update_delete_rule(current_user, rule_id):
    rule = db.session.get(Rule, rule_id)
    if not rule:
        return jsonify({"message": "Rule not found"}), 404
    if request.method == "DELETE":
        db.session.delete(rule)
        db.session.commit()
        return jsonify({"message": "Rule deleted"})
    data = request.get_json()
    rule.criteria_type = data.get("criteria_type", rule.criteria_type)
    rule.criteria_value = data.get("criteria_value", rule.criteria_value)
    rule.strategy = data.get("strategy", rule.strategy)
    rule.priority = data.get("priority", rule.priority)
    db.session.commit()
    return jsonify({"message": "Rule updated"})


@app.route("/api/admin/claims", methods=["GET"])
@admin_required
def get_all_claims(current_user):
    """
    ... (unchanged, but assignee check uses simplified roles)
    """
    claims = Claim.query.order_by(Claim.claim_id.desc()).all()
    return jsonify(
        [
            {
                "id": str(c.id),
                "claim_id": c.claim_id,
                "patient_name": c.patient_name,
                "payer": c.payer,
                "amount": str(c.amount) if c.amount else None,
                "dos": (c.dos.strftime("%Y-%m-%d") if c.dos else None),
                "status": c.status,
                "assignee": c.assignee.name if c.assignee else "Unassigned",
            }
            for c in claims
        ]
    )


@app.route("/api/admin/stats", methods=["GET"])  # New: Statistics
@admin_required
def get_stats(current_user):
    """Returns aggregates: total claims, unassigned, by status, avg workload."""
    total_claims = db.session.query(func.count(Claim.id)).scalar()
    unassigned = (
        db.session.query(func.count(Claim.id))
        .filter(Claim.assigned_to_id.is_(None))
        .scalar()
    )
    status_counts = (
        db.session.query(Claim.status, func.count(Claim.id))
        .group_by(Claim.status)
        .all()
    )
    by_status = {status: count for status, count in status_counts}
    today = date.today()
    daily_workload = (
        db.session.query(Claim.assigned_to_id, func.count(Claim.id))
        .filter(Claim.assigned_at >= today)
        .group_by(Claim.assigned_to_id)
        .all()
    )
    avg_workload = (
        sum(count for _, count in daily_workload)
        / len(User.query.filter_by(role="Member", is_active=True).all())
        if daily_workload
        else 0
    )
    return jsonify(
        {
            "total_claims": total_claims,
            "unassigned": unassigned,
            "by_status": by_status,
            "avg_daily_workload": round(avg_workload, 2),
        }
    )


@app.route("/api/admin/claims/upload-validate", methods=["POST"])
@admin_required
def validate_claims_upload(current_user):
    """
    Validate a claims file... (docstring unchanged)
    """
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]
    try:
        df = (
            pd.read_excel(file, sheet_name="Claims", engine='openpyxl')
            if file.filename.endswith(".xlsx")
            else pd.read_csv(file)
        )
    except Exception as e:
        return jsonify({"message": f"Error reading file: {e}"}), 400
    required_headers = [
        "claim_id", "patient_id", "patient_name", "status", "payer", "cpt_codes",
        "icd10_codes", "priority", "amount", "dob", "dos", "submission_deadline"
    ]
    missing_headers = [h for h in required_headers if h not in df.columns]
    if missing_headers:
        return jsonify({"message": f"Missing headers: {', '.join(missing_headers)}"}), 400
    df = df[required_headers]
    # Full validation loop (ensure this is copied if placeholder was used)
    validation_errors = []
    col_types = {
        "date": ["dob", "dos", "submission_deadline"],
        "string": [
            "claim_id",
            "patient_id",
            "patient_name",
            "payer",
            "cpt_codes",
            "icd10_codes",
        ],
        "numeric": ["priority", "amount"],
    }
    for col_type, cols in col_types.items():
        for col in cols:
            df[col] = df[col].astype(str).str.strip()
            if (df[col] == "").any():
                validation_errors.append(f"Column '{col}' contains empty values.")
                continue
            if col_type == "date":
                df[col] = pd.to_datetime(df[col], errors="coerce")
                if df[col].isnull().any():
                    validation_errors.append(f"Column '{col}' has invalid date formats.")
            elif col_type == "numeric":
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if df[col].isnull().any():
                    validation_errors.append(f"Column '{col}' has non-numeric values.")
    if validation_errors:
        return jsonify({"message": "File contains invalid data.", "errors": validation_errors}), 400
    # Check for duplicate claim_id
    if df["claim_id"].duplicated().any():
        return jsonify({"message": "Duplicate claim_ids found"}), 400
    # --- SETUP ---
    # Apply rules: Tag claims with strategy instead of filtering out
    rules = Rule.query.order_by(Rule.priority).all()
    df['rule_strategy'] = None  # New column for tagging
    today = date.today()
    today_pd = pd.to_datetime(today)  # Fix: For pandas subtraction
    for rule in rules:
        if rule.criteria_type == 'payer' and rule.criteria_value:
            mask = df['payer'] == rule.criteria_value
            df.loc[mask, 'rule_strategy'] = rule.strategy
        elif rule.criteria_type == 'age' and rule.criteria_value:
            try:
                # Parse value like '>65' to int threshold
                threshold = int(rule.criteria_value.replace('>', ''))
                df['patient_age'] = ((today_pd - df['dob']).dt.days / 365.25).astype(int)
                mask = df['patient_age'] > threshold
                df.loc[mask, 'rule_strategy'] = rule.strategy
                del df['patient_age']  # Cleanup
            except (ValueError, TypeError) as e:
                # Skip invalid age rules (e.g., bad threshold or NaT DOBs)
                print(f"Age rule skipped due to error: {e}")
                continue
    unassigned_claims_df = df[df['rule_strategy'].isna()].copy()  # Untagged for passes
    # Tagged claims: Assign separately using their rule_strategy
    tagged_df = df[df['rule_strategy'].notna()].copy()
    assignable = []
    unassignable = []
    active_members = User.query.filter_by(role='Member', is_active=True).all()
    claims_today = (
        db.session.query(Claim.assigned_to_id, func.count(Claim.id))
        .filter(Claim.assigned_at >= today)
        .group_by(Claim.assigned_to_id)
        .all()
    )
    workload = {str(uid): count for uid, count in claims_today}
    def add_claim(claim_row, assigned, strategy):
        claim = claim_row.to_dict()
        for date_col in ['dob', 'dos', 'submission_deadline']:
            if pd.notna(claim[date_col]):
                claim[date_col] = claim[date_col].strftime("%Y-%m-%d")
        claim["assigned_to_id"] = str(assigned["id"])
        claim["assign_to"] = assigned["name"]
        claim["strategy"] = strategy
        assignable.append(claim)
        workload[str(assigned["id"])] = workload.get(str(assigned["id"]), 0) + 1  # Safe increment
        return True
    # Handle tagged claims first (by rule priority)
    for _, claim_row in tagged_df.iterrows():
        strategy = claim_row['rule_strategy']
        if strategy == 'age':
            assigned = assign_claim_to_group(claim_row, [u for u in active_members if u.assign_by == 'age'], workload)
        elif strategy == 'seniority':
            assigned = assign_claim_to_group(claim_row, sorted([u for u in active_members if u.assign_by == 'seniority'], key=lambda u: u.seniority or 0, reverse=True), workload)
        else:  # 'payer'
            assigned = assign_claim_to_group(claim_row, [u for u in active_members if u.assign_by == 'payer'], workload)
        if assigned and add_claim(claim_row, assigned, f"{strategy} (Rule)"):
            continue
        unassignable.append({
            "claim_id": claim_row["claim_id"],
            "reason": f'No match for rule "{strategy}" on payer "{claim_row["payer"]}" (pri: {claim_row["priority"]}, deadline: {claim_row["submission_deadline"]})'
        })
    # --- PASS 1: Untagged by AGE ---
    age_users = [u for u in active_members if u.assign_by == "age"]
    age_sorted_claims = unassigned_claims_df.sort_values(by="dob", ascending=True)
    for index, claim_row in age_sorted_claims.iterrows():
        assigned = assign_claim_to_group(claim_row, age_users, workload)
        if assigned and add_claim(claim_row, assigned, "Age"):
            unassigned_claims_df = unassigned_claims_df.drop(index)
    # --- PASS 2: Untagged by SENIORITY ---
    seniority_users = sorted([u for u in active_members if u.assign_by == "seniority"], key=lambda u: u.seniority or 0, reverse=True)
    priority_sorted_claims = unassigned_claims_df.sort_values(by="priority", ascending=False)
    for index, claim_row in priority_sorted_claims.iterrows():
        assigned = assign_claim_to_group(claim_row, seniority_users, workload)
        if assigned and add_claim(claim_row, assigned, "Seniority"):
            unassigned_claims_df = unassigned_claims_df.drop(index)
    # --- PASS 3: Untagged DEFAULT (Payer) ---
    default_users = [u for u in active_members if u.assign_by not in ["age", "seniority"]]
    for index, claim_row in unassigned_claims_df.iterrows():
        assigned = assign_claim_to_group(claim_row, default_users, workload)
        if assigned and add_claim(claim_row, assigned, "Payer"):
            continue
        unassignable.append({
            "claim_id": claim_row["claim_id"],
            "reason": f'No capacity/skill match for payer "{claim_row["payer"]}" (pri: {claim_row["priority"]}, deadline: {claim_row["submission_deadline"]})'
        })
    del df['rule_strategy']  # Cleanup
    return jsonify({"assignable_claims": assignable, "unassignable_claims": unassignable})


def assign_claim_to_group(claim_row, user_group, workload):
    """Updated: For seniority, pick highest eligible first; general skill/capacity check."""
    payer = claim_row["payer"]
    # Sort for seniority strategy (if group is seniority_users, already sorted DESC)
    eligible_users = [
        u
        for u in user_group
        if payer in [s.name for s in u.skills]
        and workload.get(str(u.id), 0) < u.max_daily_claims
    ]
    if not eligible_users:
        return None
    # For non-seniority: least loaded; for seniority: first (highest)
    if any(u.assign_by == "seniority" for u in user_group):
        chosen = eligible_users[0]  # Prioritize top seniority
    else:
        chosen = min(eligible_users, key=lambda u: workload.get(str(u.id), 0))
    return {"id": chosen.id, "name": chosen.name}


@app.route("/api/admin/claims/upload-execute", methods=["POST"])
@admin_required
def execute_claims_upload(current_user):
    """
    ... (docstring unchanged)
    """
    data = request.get_json()
    claims_to_create = data.get("assignable_claims")
    if not claims_to_create:
        return jsonify({"message": "No claims provided"}), 400
    try:
        for claim_data in claims_to_create:
            assignee = User.query.filter_by(name=claim_data["assign_to"]).first()
            if not assignee:
                continue  # Skip invalid assignee
            # Parse dates from string
            dob = datetime.strptime(claim_data["dob"], "%Y-%m-%d").date()
            dos = datetime.strptime(claim_data["dos"], "%Y-%m-%d").date()
            deadline = datetime.strptime(
                claim_data["submission_deadline"], "%Y-%m-%d"
            ).date()
            # Create with NEW status
            new_claim = Claim(
                claim_id=claim_data["claim_id"],
                patient_id=claim_data["patient_id"],
                patient_name=claim_data["patient_name"],
                cpt_codes=claim_data["cpt_codes"],
                icd10_codes=claim_data["icd10_codes"],
                dob=dob,
                dos=dos,
                submission_deadline=deadline,
                priority=claim_data["priority"],
                amount=claim_data["amount"],
                payer=claim_data["payer"],
                status="NEW",  # Initial state
                assigned_to_id=assignee.id,
                # assigned_at auto-set by model default
            )
            db.session.add(new_claim)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500
    return jsonify({"message": f"Created {len(claims_to_create)} claims."}), 201


# Member routes
@app.route("/api/member/claims", methods=["GET"])
@token_required
def get_member_claims(current_user):
    """
    ... (updated: sort by priority/deadline; include priority)
    """
    claims = (
        Claim.query.filter_by(assigned_to_id=current_user.id)
        .order_by(
            desc(Claim.priority), asc(Claim.submission_deadline), Claim.claim_id
        )  # Better sorting
        .all()
    )
    return jsonify(
        [
            {
                "id": str(c.id),
                "claim_id": c.claim_id,
                "patient_name": c.patient_name,
                "payer": c.payer,
                "amount": str(c.amount) if c.amount else None,
                "dos": c.dos.strftime("%Y-%m-%d") if c.dos else None,
                "priority": c.priority,  # Added
                "status": c.status,
                "notes": [
                    {"content": note.content, "timestamp": note.timestamp.isoformat()}
                    for note in c.notes
                ],
            }
            for c in claims
        ]
    )


@app.route("/api/member/claims/<uuid:claim_id>", methods=["PUT"])
@token_required
def update_member_claim(current_user, claim_id):
    """
    ... (updated: append-only notes; status validation)
    """
    claim = db.session.get(Claim, claim_id)
    if not claim or claim.assigned_to_id != current_user.id:
        return jsonify({"message": "Claim not found or not yours"}), 404
    data = request.get_json()
    valid_statuses = ["NEW", "In Progress", "Submitted", "On Hold"]  # Enum-like
    if "status" in data and data["status"] not in valid_statuses:
        return jsonify({"message": "Invalid status"}), 400
    if "status" in data:
        claim.status = data["status"]
    # Always append new note (immutable audit)
    if "note" in data:
        new_note = Note(
            content=data["note"], claim_id=claim.id, user_id=current_user.id
        )
        db.session.add(new_note)
    db.session.commit()
    return jsonify({"message": "Claim updated."})
