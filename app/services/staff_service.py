from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import User, UserRole, AuditLog
from services.auth_service import hash_password
from utils.validators import Validator

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
        u_res = Validator.validate_username(username)
        if not u_res.is_valid:
            raise ValueError(u_res.error)
        clean_username = u_res.value

        n_res = Validator.validate_required_text(name, field_name="ชื่อ-นามสกุล", min_len=2, max_len=100)
        if not n_res.is_valid:
            raise ValueError(n_res.error)
        clean_name = n_res.value

        p_res = Validator.validate_password(password, min_len=4)
        if not p_res.is_valid:
            raise ValueError(p_res.error)

        ph_res = Validator.validate_phone(phone, required=False)
        if not ph_res.is_valid:
            raise ValueError(ph_res.error)
        clean_phone = ph_res.value
        
        # Check if username already exists
        existing = db.query(User).filter(User.username == clean_username).first()
        if existing:
            raise ValueError(f"ชื่อผู้ใช้ '{clean_username}' ถูกใช้งานแล้ว กรุณาใช้ชื่ออื่น")

        pw_hash = hash_password(password.strip())
        new_user = User(
            username=clean_username,
            name=clean_name,
            password_hash=pw_hash,
            role=role,
            phone=clean_phone,
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
        n_res = Validator.validate_required_text(name, field_name="ชื่อ-นามสกุล", min_len=2, max_len=100)
        if not n_res.is_valid:
            raise ValueError(n_res.error)

        ph_res = Validator.validate_phone(phone, required=False)
        if not ph_res.is_valid:
            raise ValueError(ph_res.error)

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"ไม่พบข้อมูลพนักงาน ID {user_id}")

        user.name = n_res.value
        user.role = role
        user.phone = ph_res.value
        user.is_active = is_active

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, new_password: str) -> bool:
        p_res = Validator.validate_password(new_password, min_len=4)
        if not p_res.is_valid:
            raise ValueError(p_res.error)

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
