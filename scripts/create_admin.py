# scripts/create_admin.py
import sys
from app.db import Base, SessionLocal, engine
from app.models import User, Role, UserRole
from app.security import hash_password

def main(email: str, password: str):
    # Crea las tablas si no existen
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Verifica si el rol "admin" existe
        admin_role = db.query(Role).filter_by(name="admin").first()
        if not admin_role:
            admin_role = Role(name="admin")
            db.add(admin_role)
            db.commit()
            db.refresh(admin_role)
            print(" Rol 'admin' creado.")

        # Verifica si el usuario existe
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=hash_password(password),
                active=True  # 👈 cambio aquí (antes decía is_active)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f" Usuario '{email}' creado.")
        else:
            print(f" El usuario '{email}' ya existe.")

        # Asigna rol si no lo tiene
        existing_link = db.query(UserRole).filter_by(user_id=user.id, role_id=admin_role.id).first()
        if not existing_link:
            db.add(UserRole(user_id=user.id, role_id=admin_role.id))
            db.commit()
            print(f" Rol 'admin' asignado a '{email}'.")
        else:
            print(f"ℹ El usuario '{email}' ya tiene el rol 'admin'.")

        print(" Admin listo:", email)

    except Exception as e:
        db.rollback()
        print(" Error:", e)

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m scripts.create_admin <email> <password>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
