import bcrypt
from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import User, UserRole, AuditLog

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False

class AuthService:
    ROLE_ACTION_ROUTES = {
        "OWNER": ("/admin/reports", "/admin/stock", "/admin/audit"),
        "MANAGER": ("/admin/stock", "/admin/staff", "/admin/audit"),
        "CASHIER": ("/tables", "/pos", "/admin/reports"),
        "WAITER": ("/tables", "/pos", "/kds"),
        "KITCHEN": ("/kds",),
    }

    @staticmethod
    def get_role_action_routes(user_role: UserRole) -> List[str]:
        """Return the classroom primary actions for a role's home workspace."""
        role = getattr(user_role, "value", user_role)
        return list(AuthService.ROLE_ACTION_ROUTES.get(str(role), ("/login",)))

    @staticmethod
    def get_role_home_route(user_role: UserRole) -> str:
        """Return the classroom workspace intended for each role."""
        role = getattr(user_role, "value", user_role)
        return {
            "OWNER": "/admin",
            "MANAGER": "/admin",
            "KITCHEN": "/kds",
            "CASHIER": "/tables",
            "WAITER": "/tables",
        }.get(str(role), "/login")

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """
        Authenticates a user by username and password.
        Returns the User object if successful, None otherwise.
        """
        if not username or not password:
            return None

        clean_username = username.strip().lower()
        user = db.query(User).filter(
            User.username == clean_username,
            User.is_active == True
        ).first()

        if not user:
            return None

        if check_password(password, user.password_hash):
            # Log audit for login
            log = AuditLog(
                user_id=user.id,
                action="LOGIN_PASSWORD",
                target_type="User",
                target_id=user.id
            )
            db.add(log)
            db.commit()
            return user

        return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def has_permission(user_role: UserRole, allowed_roles: List[UserRole]) -> bool:
        return user_role in allowed_roles
