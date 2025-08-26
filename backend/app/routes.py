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
    """
    Registers a new user.

    Request Body:
        {
            "name": str,
            "username": str,
            "password": str
        }

    Returns:
        {
            "message": str
        }

    Status Codes:
        201: User registered. Waiting for admin approval.
        409: Username already exists
    """

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
    """
    Logs in a user.

    Request Body:
        {
            "username": str,
            "password": str
        }

    Returns:
        {
            "token": str (JSON Web Token),
            "user": {
                "name": str,
                "role": str
            }
        }

    Raises:
        401: Invalid credentials
        403: Account is not active
    """
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
    """
    Returns a list of all non-admin users in the database.

    Each user is represented as a JSON object with the following keys:

    * id (string): The UUID of the user.
    * name (string): The name of the user.
    * username (string): The username of the user.
    * role (string): The role of the user (Biller, Member, or Admin).
    * is_active (bool): Whether the user is active or not.
    * skills (list of strings): The skills of the user.
    * max_daily_claims (int): The maximum number of claims the user can be assigned to in a day.
    * seniority (int): The seniority of the user.
    * assign_by (string): The assignment strategy for the user (payer or submitter).

    :param current_user: The current user object, passed by the admin_required decorator.
    :return: A JSON response containing the list of users.
    """
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
    """
    API endpoint to update an existing user.

    The request body should contain the key-value pairs of the fields to be updated.
    The fields to be updated can be any of the following:

    * role (string): The new role for the user. Can be "Biller", "Admin", or "Member".
    * max_daily_claims (int): The new maximum number of claims the user can be assigned to in a day.
    * seniority (int): The new seniority of the user.
    * is_active (bool): Whether the user should be active or not.
    * assign_by (string): The new assignment strategy for the user. Can be "payer" or "submitter".
    * skill_ids (list of uuid): The new skills for the user.

    Returns a JSON response with a message indicating whether the update was successful or not.
    """
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
    """
    API endpoint to get all skills in the database.

    Returns a JSON response containing a list of objects, each with an "id" and a "name" key.
    """
    skills = Skill.query.all()
    return jsonify([{"id": str(s.id), "name": s.name} for s in skills])


# Find the existing get_all_claims function and replace it with this version
@app.route("/api/admin/claims", methods=["GET"])
@admin_required
def get_all_claims(current_user):
    """
    API endpoint to get all claims in the database.

    Returns a JSON list of objects with the following attributes:

    - id: The ID of the claim (UUID)
    - claim_id: The claim ID (string)
    - patient_name: The patient name (string)
    - payer: The payer name (string)
    - amount: The amount (integer, or None if not applicable)
    - dos: The date of service (string, or None if not applicable)
    - status: The status of the claim (string)
    - assignee: The name of the member assigned to the claim (string, or "Unassigned" if not assigned)

    The list is sorted first by claim ID (newest first).

    :return:
        A JSON response containing a list of all claims in the database.
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
                "dos": (
                    c.dos.strftime("%Y-%m-%d") if c.dos else None
                ),  # Format date for readability
                "status": c.status,
                "assignee": c.assignee.name if c.assignee else "Unassigned",
            }
            for c in claims
        ]
    )


@app.route("/api/admin/claims/upload-validate", methods=["POST"])
@admin_required
def validate_claims_upload(current_user):
    """
    Validate a claims file uploaded by an admin and propose a claim assignment plan.

    The file is expected to be a CSV or Excel file with the following columns:
    - claim_id
    - patient_id
    - patient_name
    - payer
    - cpt_codes
    - icd10_codes
    - amount
    - dos
    - submission_deadline
    - status

    The endpoint will validate the file and simulate the assignment of claims to members
    based on the configuration of the members and the claims. The response will contain
    a list of claims that can be assigned and a list of claims that cannot be assigned
    with reasons why.

    The assignment plan is determined by the following rules:
    1. Assign by age: Assign claims to the oldest members first.
    2. Assign by seniority: Assign claims to the most senior members first.
    3. Assign by payer: Assign claims to members with the required skill set.

    :return:
        A JSON response with two keys: 'assignable_claims' and 'unassignable_claims'.
        'assignable_claims' contains a list of dictionaries with the following keys:
        - claim_id
        - patient_name
        - payer
        - amount
        - dos
        - submission_deadline
        - status
        - assign_to (name of the user to assign the claim to)
        - strategy (name of the assignment strategy used)

        'unassignable_claims' contains a list of dictionaries with the following keys:
        - claim_id
        - reason (a string describing why the claim cannot be assigned)
    """
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
    """
    Executes the assignment plan proposed during the validation step.

    This endpoint expects a JSON payload with a key named 'assignable_claims' containing
    an array of objects representing the claims to be assigned. Each object should contain
    the following fields:

    - claim_id
    - patient_id
    - patient_name
    - cpt_codes
    - icd10_codes
    - dob
    - dos
    - submission_deadline
    - priority
    - amount
    - payer
    - assign_to (name of the user to assign the claim to)

    The endpoint will create a new Claim object for each claim in the payload, assign the
    claim to the specified user, and commit the transaction. If any error occurs during
    the process, the transaction will be rolled back and a 500 error will be returned.

    :return:
        A JSON response with a message indicating the number of claims created and assigned.
    """
    data = request.get_json()
    # To be consistent with the validation step, we expect a key named 'assignable_claims'
    claims_to_create = data.get("assignable_claims")

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
                    status="Assigned",  # Set the status upon successful assignment
                    assigned_to_id=assignee.id,
                )
                db.session.add(new_claim)

        # Commit the transaction once all claims have been added
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        # Provide a more specific error message for debugging
        return (
            jsonify({"message": f"An error occurred during database commit: {str(e)}"}),
            500,
        )

    return (
        jsonify(
            {
                "message": f"Successfully assigned and created {len(claims_to_create)} claims."
            }
        ),
        201,
    )


# API endpoint to get member claims
@app.route("/api/member/claims", methods=["GET"])
@token_required
def get_member_claims(current_user):
    """
    API endpoint to get the claims assigned to the current member.

    Returns a JSON list of objects with the following attributes:

    - id: The ID of the claim (UUID)
    - claim_id: The claim ID (string)
    - patient_name: The patient name (string)
    - payer: The payer name (string)
    - amount: The amount (integer, or None if not applicable)
    - dos: The date of service (string, or None if not applicable)
    - status: The status of the claim (string)
    - notes: A list of notes, with each note containing a content string and a timestamp (ISO 8601 string)

    The list is sorted first by status, then by claim ID.
    """

    claims = (
        Claim.query.filter_by(assigned_to_id=current_user.id)
        .order_by(Claim.status, Claim.claim_id)
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
                "status": c.status,
                "notes": [
                    {"content": note.content, "timestamp": note.timestamp.isoformat()}
                    for note in c.notes
                ],
            }
            for c in claims
        ]
    )


# API endpoint to update a claim
@app.route("/api/member/claims/<uuid:claim_id>", methods=["PUT"])
@token_required
def update_member_claim(current_user, claim_id):
    """
    API endpoint to update a member claim.

    Updates a claim's status and/or the most recent note for that claim.

    Args:
        claim_id (uuid): The ID of the claim to update.

    Returns:
        A JSON response containing a message indicating the result of the update.
    """
    claim = db.session.get(Claim, claim_id)
    if not claim or claim.assigned_to_id != current_user.id:
        return jsonify({"message": "Claim not found or not assigned to you"}), 404

    data = request.get_json()
    if "status" in data:
        claim.status = data["status"]

    # NEW LOGIC: Update the most recent note, or create a new one
    if "note" in data:
        # Find the most recent note for this claim
        latest_note = (
            Note.query.filter_by(claim_id=claim.id)
            .order_by(Note.timestamp.desc())
            .first()
        )

        if latest_note:
            # If a note exists, update its content
            latest_note.content = data["note"]
        else:
            # If no note exists, create a new one
            new_note = Note(
                content=data["note"], claim_id=claim.id, user_id=current_user.id
            )
            db.session.add(new_note)

    db.session.commit()
    return jsonify({"message": "Claim updated."})
