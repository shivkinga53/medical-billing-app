from flask import jsonify, request, current_app as app
from . import db
from .models import User, Claim, Skill, Note
from .auth_utils import token_required, admin_required
from sqlalchemy import func
import bcrypt
import jwt
from datetime import datetime, timedelta
import pandas as pd
import os


# --- Authentication ---
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"message": "Username already exists"}), 409

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
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    print(data)
    print(user.__dict__)
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
        print(jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"]))
        return jsonify({"token": token, "user": {"name": user.name, "role": user.role}})
    return jsonify({"message": "Invalid credentials"}), 401


# --- Admin Routes ---
@app.route("/api/admin/users", methods=["GET"])
@admin_required
def get_users(current_user):
    users = User.query.filter(User.role != "Admin").all()
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
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    user.role = data.get("role", user.role)
    user.max_daily_claims = data.get("max_daily_claims", user.max_daily_claims)
    user.seniority = data.get("seniority", user.seniority)
    user.is_active = data.get("is_active", user.is_active)
    user.assign_by = data.get("assign_by", user.assign_by)

    if "skill_ids" in data:
        user.skills = Skill.query.filter(Skill.id.in_(data["skill_ids"])).all()

    db.session.commit()
    return jsonify({"message": "User updated successfully."})


@app.route("/api/admin/skills", methods=["GET"])
@admin_required
def get_skills(current_user):
    skills = Skill.query.all()
    return jsonify([{"id": str(s.id), "name": s.name} for s in skills])


@app.route("/api/admin/claims/upload-validate", methods=["POST"])
@admin_required
def validate_claims_upload(current_user):
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files["file"]

    try:
        df = (
            pd.read_excel(file, sheet_name="Claims")
            if file.filename.endswith(".xlsx")
            else pd.read_csv(file)
        )
    except Exception as e:
        return jsonify({"message": f"Error reading file: {e}"}), 400

    required_headers = [
        "claim_id",
        "patient_id",
        "patient_name",
        "status",
        "payer",
        "cpt_codes",
        "icd10_codes",
        "priority",
        "amount",
        "dob",
        "dos",
        "submission_deadline",
    ]

    missing_headers = [h for h in required_headers if h not in df.columns]
    if missing_headers:
        return (
            jsonify(
                {
                    "message": f"File is missing required headers ({', '.join(missing_headers)})."
                }
            ),
            400,
        )

    df = df[required_headers]

    # REFACTORED: Simplified Data Validation
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
            # Check for empty strings after stripping
            if (df[col] == "").any():
                validation_errors.append(f"Column '{col}' contains empty values.")
                continue  # Skip further checks for this column

            if col_type == "date":
                df[col] = pd.to_datetime(df[col], errors="coerce")
                if df[col].isnull().any():
                    validation_errors.append(
                        f"Column '{col}' has invalid date formats."
                    )
            elif col_type == "numeric":
                df[col] = pd.to_numeric(df[col], errors="coerce")
                if df[col].isnull().any():
                    validation_errors.append(f"Column '{col}' has non-numeric values.")

    if validation_errors:
        return (
            jsonify(
                {"message": "File contains invalid data.", "errors": validation_errors}
            ),
            400,
        )

    # --- SETUP ---
    unassigned_claims_df = df.copy()
    assignable = []
    unassignable = []

    active_members = User.query.filter_by(is_active=True).all()
    claims_today = (
        db.session.query(Claim.assigned_to_id, func.count(Claim.id))
        .group_by(Claim.assigned_to_id)
        .all()
    )
    workload = {str(uid): count for uid, count in claims_today}

    # --- PASS 1: ASSIGN BY AGE ---
    age_users = [u for u in active_members if u.assign_by == "age"]
    sr_billers = [u for u in age_users if u.role and "Sr. Biller" in u.role]
    billers = [
        u
        for u in age_users
        if u.role and "Biller" in u.role and "Sr. Biller" not in u.role
    ]
    age_sorted_claims = unassigned_claims_df.sort_values(by="dob", ascending=True)

    claims_to_remove_indices = []
    for index, claim_row in age_sorted_claims.iterrows():
        assigned = assign_claim_to_group(
            claim_row, sr_billers, workload
        ) or assign_claim_to_group(claim_row, billers, workload)
        if assigned:
            claim = claim_row.to_dict()
            claim["assigned_to_id"] = assigned["id"]
            claim["assign_to"] = assigned[
                "name"
            ]  # BUG FIX: Changed from a tuple to a string
            claim["strategy"] = "Age"
            assignable.append(claim)
            workload[str(assigned["id"])] = workload.get(str(assigned["id"]), 0) + 1
            claims_to_remove_indices.append(index)
    unassigned_claims_df = unassigned_claims_df.drop(claims_to_remove_indices)

    # --- PASS 2: ASSIGN BY SENIORITY ---
    seniority_users = sorted(
        [u for u in active_members if u.assign_by == "seniority"],
        key=lambda u: u.seniority or 0,
        reverse=True,
    )
    priority_sorted_claims = unassigned_claims_df.sort_values(
        by="priority", ascending=False
    )

    claims_to_remove_indices = []
    for index, claim_row in priority_sorted_claims.iterrows():
        assigned = assign_claim_to_group(claim_row, seniority_users, workload)
        if assigned:
            claim = claim_row.to_dict()
            claim["assigned_to_id"] = assigned["id"]
            claim["assign_to"] = assigned[
                "name"
            ]  # BUG FIX: Changed from a tuple to a string
            claim["strategy"] = "Seniority"
            assignable.append(claim)
            workload[str(assigned["id"])] = workload.get(str(assigned["id"]), 0) + 1
            claims_to_remove_indices.append(index)
    unassigned_claims_df = unassigned_claims_df.drop(claims_to_remove_indices)

    # --- PASS 3: DEFAULT ROUND-ROBIN ---
    default_users = [
        u for u in active_members if u.assign_by not in ["age", "seniority"]
    ]
    for index, claim_row in unassigned_claims_df.iterrows():
        assigned = assign_claim_to_group(claim_row, default_users, workload)
        if assigned:
            claim = claim_row.to_dict()
            claim["assigned_to_id"] = assigned["id"]
            claim["assign_to"] = assigned[
                "name"
            ]  # BUG FIX: Changed from a tuple to a string
            claim["strategy"] = "Payer"
            assignable.append(claim)
            workload[str(assigned["id"])] = workload.get(str(assigned["id"]), 0) + 1
        else:
            unassignable.append(
                {
                    "claim_id": claim_row["claim_id"],
                    "reason": f'No active member with skill "{claim_row["payer"]}" and available capacity.',
                }
            )

    return jsonify(
        {"assignable_claims": assignable, "unassignable_claims": unassignable}
    )


# Helper function to be placed inside routes.py or a utils file
def assign_claim_to_group(claim_row, user_group, workload):
    """Finds an eligible user in a group for a given claim."""
    payer = claim_row["payer"]
    eligible_users = [
        u
        for u in user_group
        if payer in [s.name for s in u.skills]
        and (workload.get(str(u.id), 0) < u.max_daily_claims)
    ]

    if not eligible_users:
        return None

    # Simple round-robin: choose the one with the least work so far
    chosen = min(eligible_users, key=lambda u: workload.get(str(u.id), 0))
    return {"id": chosen.id, "name": chosen.name}


@app.route("/api/admin/claims/upload-execute", methods=["POST"])
@admin_required
def execute_claims_upload(current_user):
    data = request.get_json()
    # To be consistent with the validation step, we expect a key named 'assignable_claims'
    claims_to_create = data.get("claims")

    if not claims_to_create:
        return jsonify({"message": "No claims provided to execute."}), 400

    try:
        for claim_data in claims_to_create:
            assignee = User.query.filter_by(name=claim_data["assign_to"]).first()
            if assignee:
                # Create the new Claim object with all required fields from the validated data
                new_claim = Claim(
                    claim_id=claim_data["claim_id"],
                    patient_id=claim_data["patient_id"],
                    patient_name=claim_data["patient_name"],
                    cpt_codes=claim_data["cpt_codes"],
                    icd10_codes=claim_data["icd10_codes"],
                    dob=claim_data["dob"],
                    dos=claim_data["dos"],
                    submission_deadline=claim_data["submission_deadline"],
                    priority=claim_data["priority"],
                    amount=claim_data["amount"],
                    payer=claim_data["payer"],
                    status='Assigned',  # Set the status upon successful assignment
                    assigned_to_id=assignee.id
                )
                db.session.add(new_claim)
        
        # Commit the transaction once all claims have been added
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        # Provide a more specific error message for debugging
        return jsonify({"message": f"An error occurred during database commit: {str(e)}"}), 500

    return jsonify({"message": f"Successfully assigned and created {len(claims_to_create)} claims."}), 201


# --- Member Routes ---
@app.route("/api/member/claims", methods=["GET"])
@token_required
def get_member_claims(current_user):
    # Members can log in to view the claims assigned to them
    claims = Claim.query.filter_by(assigned_to_id=current_user.id).all()
    return jsonify(
        [
            {
                "id": str(c.id),
                "claim_id": c.claim_id,
                "patient_name": c.patient_name,
                "payer": c.payer,
                "status": c.status,
            }
            for c in claims
        ]
    )


@app.route("/api/member/claims/<uuid:claim_id>", methods=["PUT"])
@token_required
def update_member_claim(current_user, claim_id):
    # Members can update status... and add notes
    claim = db.session.get(Claim, claim_id)
    if not claim or claim.assigned_to_id != current_user.id:
        return jsonify({"message": "Claim not found or not assigned to you"}), 404

    data = request.get_json()
    if "status" in data:
        claim.status = data["status"]
    if "note" in data:
        new_note = Note(
            content=data["note"], claim_id=claim.id, user_id=current_user.id
        )
        db.session.add(new_note)

    db.session.commit()
    return jsonify({"message": "Claim updated."})
