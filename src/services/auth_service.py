from typing import Optional
from sqlalchemy.orm import Session
from src.models.user import User
from src.core.security import get_password_hash, verify_password

class AuthService:
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.strip().lower()).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @classmethod
    def register_user(cls, db: Session, name: str, email: str, password: str) -> User:
        email_clean = email.strip().lower()
        if cls.get_user_by_email(db, email_clean):
            raise ValueError("Email já cadastrado no sistema.")
        
        user = User(
            name=name.strip(),
            email=email_clean,
            password_hash=get_password_hash(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> Optional[User]:
        user = cls.get_user_by_email(db, email)
        if not user or not verify_password(password, user.password_hash):
            return None
        return user

    @classmethod
    def get_or_create_default_user(cls, db: Session) -> User:
        """Garante a existência de um usuário local padrão para uso direto e sem fricção."""
        user = db.query(User).first()
        if not user:
            user = cls.register_user(
                db=db,
                name="Usuário Pessoal",
                email="admin@local.com",
                password="admin",
            )
        return user
