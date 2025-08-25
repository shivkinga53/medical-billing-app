from . import db
from sqlalchemy.dialects.postgresql import UUID
import uuid

user_skills = db.Table('user_skills',
    db.Column('user_id', UUID(as_uuid=True), db.ForeignKey('users.id'), primary_key=True),
    db.Column('skill_id', UUID(as_uuid=True), db.ForeignKey('skills.id'), primary_key=True)
)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='Biller')
    max_daily_claims = db.Column(db.Integer, nullable=False, default=0)
    seniority = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    assign_by = db.Column(db.String(50), nullable=False, default='payer')
    skills = db.relationship('Skill', secondary=user_skills, lazy='subquery',
        backref=db.backref('users', lazy=True))

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Claim(db.Model):
    __tablename__ = 'claims'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_id = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.String(50), nullable=False)
    patient_name = db.Column(db.String(255))
    cpt_codes = db.Column(db.String(255))
    icd10_codes = db.Column(db.String(255))
    dob = db.Column(db.Date, nullable=False)
    dos = db.Column(db.Date, nullable=False)
    submission_deadline = db.Column(db.Date, nullable=False)
    priority = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payer = db.Column(db.String(255))
    status = db.Column(db.String(50), nullable=False, default='NEW')
    assigned_to_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    assignee = db.relationship('User', backref='claims')
    notes = db.relationship('Note', backref='claim', lazy=True)

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())
    claim_id = db.Column(UUID(as_uuid=True), db.ForeignKey('claims.id'), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)