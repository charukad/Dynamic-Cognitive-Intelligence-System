"""JWT authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from src.core import get_logger, settings

logger = get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT bearer token
security = HTTPBearer()


class JWTAuth:
    """JWT authentication handler."""

    def __init__(self):
        """Initialize JWT auth."""
        self.secret_key = settings.SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            data: Data to encode in token
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=self.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )
        
        return encoded_jwt

    def create_refresh_token(self, data: dict) -> str:
        """Create JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.algorithm,
        )
        
        return encoded_jwt

    def decode_token(self, token: str) -> dict:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token to decode
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
            )
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_current_user(
        self,
        credentials: HTTPAuthorizationCredentials = Depends(security),
    ) -> dict:
        """
        Get current authenticated user from token.
        
        Args:
            credentials: HTTP authorization credentials
            
        Returns:
            User data from token
        """
        token = credentials.credentials
        payload = self.decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        
        return {"user_id": user_id, **payload}


# Global JWT auth instance
jwt_auth = JWTAuth()


# Dependency for protected routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Dependency to get current authenticated user."""
    return await jwt_auth.get_current_user(credentials)


# Role-based access control
class RoleChecker:
    """Check user roles for authorization."""

    def __init__(self, allowed_roles: list[str]):
        """
        Initialize role checker.
        
        Args:
            allowed_roles: List of allowed roles
        """
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        """
        Check if user has required role.
        
        Args:
            current_user: Current authenticated user
            
        Returns:
            User data if authorized
            
        Raises:
            HTTPException: If user lacks required role
        """
        user_role = current_user.get("role", "user")
        
        if user_role not in self.allowed_roles:
            logger.warning(
                f"User {current_user.get('user_id')} attempted access with role {user_role}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        return current_user


# Predefined role checkers
require_admin = RoleChecker(["admin"])
require_user = RoleChecker(["user", "admin"])
