import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from database.models import User, UserRole, AuditLog

def hash_pin(pin: str) -> str:
    # Hash a password for the first time
    # Using a fixed salt or generate one. Usually, for DB we store the full hashed string.
    # In bcrypt, gensalt() generates a random salt and hashes it.
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pin.encode("utf-8"), salt).decode("utf-8")

def check_pin(pin: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False

class AuthService:
    @staticmethod
    def verify_pin(db: Session, pin: str) -> Optional[User]:
        if len(pin) != 6 or not pin.isdigit():
            return None
        
        # We need to fetch all active users and check pin since bcrypt salts are unique
        # A better way for large scale is to not allow PIN only login without user id,
        # but since this is a POS with PIN-only login, we iterate over active users
        users = db.query(User).filter(User.is_active == True).all()
        user = None
        for u in users:
            if check_pin(pin, u.pin_hash):
                user = u
                break
        
        if user:
            # Log audit for login
            log = AuditLog(user_id=user.id, action="LOGIN_PIN", target_type="User", target_id=user.id)
            db.add(log)
            db.commit()
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()
