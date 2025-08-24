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
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409
        
    hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
    new_user = User(
        name=data['name'],
        username=data['username'],
        password_hash=hashed_password.decode('utf-8')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered. Waiting for admin approval.'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    print(data)
    if user and bcrypt.checkpw(data['password'].encode('utf-8'), user.password_hash.encode('utf-8')):
        if not user.is_active:
            return jsonify({'message': 'Account is not active.'}), 403
        
        token = jwt.encode({
            'user_id': str(user.id), 'role': user.role, 'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({'token': token, 'user': {'name': user.name, 'role': user.role}})
    return jsonify({'message': 'Invalid credentials'}), 401

# --- Admin Routes ---
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_users(current_user):
    users = User.query.filter(User.role != 'Admin').all()
    return jsonify([{
        'id': str(u.id), 'name': u.name, 'username': u.username, 'role': u.role, 'is_active': u.is_active, 
        'skills': [s.name for s in u.skills], 'max_daily_claims': u.max_daily_claims, 'seniority': u.seniority,
        'assign_by': u.assign_by
    } for u in users])

@app.route('/api/admin/users/<uuid:user_id>', methods=['PUT'])
@admin_required
def update_user(current_user, user_id):
    user = db.session.get(User, user_id)
    if not user: return jsonify({'message': 'User not found'}), 404
    
    data = request.get_json()
    user.role = data.get('role', user.role)
    user.max_daily_claims = data.get('max_daily_claims', user.max_daily_claims)
    user.seniority = data.get('seniority', user.seniority)
    user.is_active = data.get('is_active', user.is_active)
    
    if 'skill_ids' in data:
        user.skills = Skill.query.filter(Skill.id.in_(data['skill_ids'])).all()
        
    db.session.commit()
    return jsonify({'message': 'User updated successfully.'})

@app.route('/api/admin/skills', methods=['GET'])
@admin_required
def get_skills(current_user):
    skills = Skill.query.all()
    return jsonify([{'id': str(s.id), 'name': s.name} for s in skills])

@app.route('/api/admin/claims/upload-validate', methods=['POST'])
@admin_required
def validate_claims_upload(current_user):
    # When Admin uploads xlsx/csv file... it should have headers like below which will be checked on upload
    if 'file' not in request.files: return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    
    try:
        df = pd.read_excel(file) if file.filename.endswith('.xlsx') else pd.read_csv(file)
    except Exception as e:
        return jsonify({'message': f'Error reading file: {e}'}), 400

    required_headers = ['claim_id', 'patient_name', 'payer']
    if not all(h in df.columns for h in required_headers):
        return jsonify({'message': 'File is missing required headers.'}), 400

    # Assignment Simulation Logic
    active_members = User.query.filter_by(is_active=True).all()
    claims_today = db.session.query(Claim.assigned_to_id, func.count(Claim.id)).group_by(Claim.assigned_to_id).all()
    workload = {str(uid): count for uid, count in claims_today}
    
    assignable = []
    unassignable = []
    
    for index, row in df.iterrows():
        payer = row['payer']
        eligible_members = [m for m in active_members if payer in [s.name for s in m.skills] and (workload.get(str(m.id), 0) < (m.max_daily_claims or 999))]
        
        if not eligible_members:
            unassignable.append({'claim_id': row['claim_id'], 'reason': f'No active member with skill "{payer}" and available capacity.'})
        else:
            # Simple assignment for validation, not round-robin yet
            assignable.append({'claim_id': row['claim_id'], 'assign_to': eligible_members[0].name})
    
    # Check if all the claims assigned to employees or not, if not then why show error
    return jsonify({'assignable_claims': assignable, 'unassignable_claims': unassignable})

@app.route('/api/admin/claims/upload-execute', methods=['POST'])
@admin_required
def execute_claims_upload(current_user):
    # After successful assigning selection proceed which will add claims...
    data = request.get_json()
    claims_to_create = data.get('claims')

    try:
        for claim_data in claims_to_create:
            assignee = User.query.filter_by(name=claim_data['assign_to']).first()
            if assignee:
                new_claim = Claim(
                    claim_id=claim_data['claim_id'],
                    patient_name=claim_data.get('patient_name'),
                    payer=claim_data.get('payer'),
                    assigned_to_id=assignee.id
                )
                db.session.add(new_claim)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'An error occurred: {e}'}), 500

    return jsonify({'message': 'Claims assigned successfully.'}), 201


# --- Member Routes ---
@app.route('/api/member/claims', methods=['GET'])
@token_required
def get_member_claims(current_user):
    # Members can log in to view the claims assigned to them
    claims = Claim.query.filter_by(assigned_to_id=current_user.id).all()
    return jsonify([{
        'id': str(c.id), 'claim_id': c.claim_id, 'patient_name': c.patient_name,
        'payer': c.payer, 'status': c.status
    } for c in claims])

@app.route('/api/member/claims/<uuid:claim_id>', methods=['PUT'])
@token_required
def update_member_claim(current_user, claim_id):
    # Members can update status... and add notes
    claim = db.session.get(Claim, claim_id)
    if not claim or claim.assigned_to_id != current_user.id:
        return jsonify({'message': 'Claim not found or not assigned to you'}), 404
    
    data = request.get_json()
    if 'status' in data:
        claim.status = data['status']
    if 'note' in data:
        new_note = Note(content=data['note'], claim_id=claim.id, user_id=current_user.id)
        db.session.add(new_note)
        
    db.session.commit()
    return jsonify({'message': 'Claim updated.'})