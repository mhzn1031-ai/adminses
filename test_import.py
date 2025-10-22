try:
    print("Testing imports...")
    from app.db import engine
    from app.models import SQLModel
    print("✓ Imports successful")
    
    print("Creating database...")
    SQLModel.metadata.create_all(engine)
    print("✓ Database created")
    
    print("\nAll checks passed! Server should work.")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
