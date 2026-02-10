"""User management system with authentication."""

import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator

from src.core import get_logger
from src.infrastructure.database.postgres_client import postgres_client

logger = get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    """User model."""
    
    id: str
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "user"  # user, admin, developer
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    last_login: Optional[datetime] = None
    
    @validator("role")
    def validate_role(cls, v):
        """Validate role is valid."""
        valid_roles = ["user", "admin", "developer", "viewer"]
        if v not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {valid_roles}")
        return v


class UserCreate(BaseModel):
    """User creation schema."""
    
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    role: str = "user"
    
    @validator("password")
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    @validator("username")
    def validate_username(cls, v):
        """Validate username format."""
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if not v.isalnum() and "_" not in v:
            raise ValueError("Username can only contain letters, numbers, and underscores")
        return v


class UserUpdate(BaseModel):
    """User update schema."""
    
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserManagementService:
    """
    User management service.
    
    Handles user CRUD, authentication, and role management.
    """

    async def init_schema(self) -> None:
        """Initialize user management schema."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR(255) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255),
            role VARCHAR(50) NOT NULL DEFAULT 'user',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        """
        
        await postgres_client.connect()
        await postgres_client.execute(schema_sql)
        logger.info("User management schema initialized")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user
        """
        # Generate user ID
        user_id = f"user_{secrets.token_urlsafe(16)}"
        
        # Hash password
        password_hash = self.hash_password(user_data.password)
        
        # Insert into database
        await postgres_client.execute(
            """
            INSERT INTO users (id, email, username, password_hash, full_name, role)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            user_id,
            user_data.email,
            user_data.username,
            password_hash,
            user_data.full_name,
            user_data.role,
        )
        
        logger.info(f"Created user: {user_data.username} (ID: {user_id})")
        
        return User(
            id=user_id,
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            role=user_data.role,
        )

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        row = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username,
        )
        
        if not row:
            return None
        
        return User(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        row = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            email,
        )
        
        if not row:
            return None
        
        return User(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            username: Username or email
            password: Plain text password
            
        Returns:
            User if authenticated, None otherwise
        """
        # Try to get user by username or email
        row = await postgres_client.fetchrow(
            """
            SELECT * FROM users 
            WHERE username = $1 OR email = $1
            """,
            username,
        )
        
        if not row:
            return None
        
        # Verify password
        if not self.verify_password(password, row["password_hash"]):
            return None
        
        # Check if user is active
        if not row["is_active"]:
            logger.warning(f"Inactive user attempted login: {username}")
            return None
        
        # Update last login
        await postgres_client.execute(
            "UPDATE users SET last_login = $1 WHERE id = $2",
            datetime.utcnow(),
            row["id"],
        )
        
        logger.info(f"User authenticated: {username}")
        
        return User(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            last_login=datetime.utcnow(),
        )

    async def update_user(self, user_id: str, update_data: UserUpdate) -> Optional[User]:
        """Update user."""
        updates = []
        params = []
        param_count = 1
        
        if update_data.full_name is not None:
            updates.append(f"full_name = ${param_count}")
            params.append(update_data.full_name)
            param_count += 1
        
        if update_data.role is not None:
            updates.append(f"role = ${param_count}")
            params.append(update_data.role)
            param_count += 1
        
        if update_data.is_active is not None:
            updates.append(f"is_active = ${param_count}")
            params.append(update_data.is_active)
            param_count += 1
        
        if not updates:
            return await self.get_user_by_id(user_id)
        
        params.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = ${param_count}"
        await postgres_client.execute(query, *params)
        
        return await self.get_user_by_id(user_id)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        row = await postgres_client.fetchrow(
            "SELECT * FROM users WHERE id = $1",
            user_id,
        )
        
        if not row:
            return None
        
        return User(
            id=row["id"],
            email=row["email"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            last_login=row["last_login"],
        )

    async def list_users(self, limit: int = 100) -> List[User]:
        """List all users."""
        rows = await postgres_client.fetch(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT $1",
            limit,
        )
        
        return [
            User(
                id=row["id"],
                email=row["email"],
                username=row["username"],
                full_name=row["full_name"],
                role=row["role"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                last_login=row["last_login"],
            )
            for row in rows
        ]

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        result = await postgres_client.execute(
            "DELETE FROM users WHERE id = $1",
            user_id,
        )
        
        return "DELETE" in result


# Global instance
user_service = UserManagementService()
