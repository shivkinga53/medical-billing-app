from flask import Blueprint
import click
from . import db
from .models import User, Skill
import bcrypt
import os

db_cli = Blueprint('db_cli', __name__)

@db_cli.cli.command('create-admin')
def create_admin():
    """Creates the initial admin user."""
    if User.query.filter_by(role='Admin').first():
        print('Admin user already exists.')
        return
    
    username = os.getenv('ADMIN_USERNAME')
    password = os.getenv('ADMIN_PASSWORD')
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    admin = User(
        name=os.getenv('ADMIN_NAME'),
        username=username,
        password_hash=hashed_password.decode('utf-8'),
        role='Admin',
        is_active=True,
        assign_by=None
    )
    db.session.add(admin)
    db.session.commit()
    print(f'Admin user created. Username: "{username}", Password: "{password}"')

@db_cli.cli.command('create-skills')
def create_skills():
    """Creates initial skills from the employees sheet."""
    if Skill.query.first():
        print('Skills already exist.')
        return
    
    skill_names = ['Medicare', 'BlueCross', 'UnitedHealth', 'Aetna', 'Medicaid', 'Kaiser', 'Cigna']
    for name in skill_names:
        db.session.add(Skill(name=name))
    db.session.commit()
    print('Initial skills created.')