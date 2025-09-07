#!/usr/bin/env python3
"""
Script to create an initial admin user for the Policy Jam application
"""
from app import create_app
from models import db, Admin

def create_admin_user():
    """Create an initial admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        existing_admin = Admin.query.filter_by(username='admin').first()
        if existing_admin:
            print("Admin user 'admin' already exists!")
            return
        
        # Create new admin user
        admin = Admin()
        admin.username = 'admin'
        admin.email = 'admin@policyjam.com'
        admin.first_name = 'System'
        admin.last_name = 'Administrator'
        admin.set_password('admin123')  # Change this in production!
        admin.role = 'super_admin'
        
        db.session.add(admin)
        db.session.commit()
        
        print("✓ Admin user created successfully!")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Email: admin@policyjam.com")
        print("  Role: super_admin")
        print("")
        print("⚠️  IMPORTANT: Change the default password after first login!")
        print("   Access admin panel at: /admin/login")

if __name__ == '__main__':
    create_admin_user()