from app.db import engine
from app.models import SQLModel

print("Creating database...")
SQLModel.metadata.create_all(engine)
print("✓ Database created successfully")

from app.auth import create_admin
from sqlmodel import Session

print("Creating admin user...")
with Session(engine) as session:
    create_admin(session, "admin", "adminpass")
print("✓ Admin user created (admin/adminpass)")

print("\nReset complete!")
