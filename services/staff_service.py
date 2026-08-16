from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import User, UserRole, AuditLog
from services.auth_service import hash_password

class StaffService:
    @staticmethod
    def get_all_staff(db: Session, active_only: bool = False) -> List[User]:
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.order_by(User.id.asc()).all()

    @staticmethod
    def get_staff_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_staff(
        db: Session,
        username: str,
        name: str,
        password: str,
        role: UserRole,
        phone: Optional[str] = None
    ) -> User:
        clean_username = username.strip().lower()
        
        # Check if username already exists
        existing = db.query(User).filter(User.username == clean_username).first()
        if existing:
            raise ValueError(f"ชื่อผู้ใช้ '{clean_username}' ถูกใช้งานแล้ว กรุณาใช้ชื่ออื่น")

        if len(password) < 4:
            raise ValueError("รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร")

        pw_hash = hash_password(password)
        new_user = User(
            username=clean_username,
            name=name.strip(),
            password_hash=pw_hash,
            role=role,
            phone=phone.strip() if phone else None,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @staticmethod
    def update_staff(
        db: Session,
        user_id: int,
        name: str,
        role: UserRole,
        phone: Optional[str] = None,
        is_active: bool = True
    ) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"ไม่พบข้อมูลพนักงาน ID {user_id}")

        user.name = name.strip()
        user.role = role
        user.phone = phone.strip() if phone else None
        user.is_active = is_active

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        if len(new_password) < 4:
            raise ValueError("รหัสผ่านใหม่ต้องมีความยาวอย่างน้อย 4 ตัวอักษร")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"ไม่พบข้อมูลพนักงาน ID {user_id}")

        user.password_hash = hash_password(new_password)
        db.commit()
        return True

    @staticmethod
    def toggle_active_status(db: Session, user_id: int) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"ไม่พบข้อมูลพนักงาน ID {user_id}")

        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)
        return user
