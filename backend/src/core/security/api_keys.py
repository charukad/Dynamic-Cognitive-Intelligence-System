"""API key management system."""

import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel, validator

from src.core import get_logger
from src.infrastructure.database.postgres_client import postgres_client

logger = get_logger(__name__)


class APIKey(BaseModel):
    """API Key model."""
    
    id: str
    user_id: str
    key_hash: str  # SHA-256 hash of the key
    name: str
    scopes: List[str] = []
    is_active: bool = True
    created_at: datetime = datetime.utcnow()
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int = 0


class APIKeyCreate(BaseModel):
    """API Key creation schema."""
    
    user_id: str
    name: str
    scopes: List[str]  = ["read"]
    expires_in_days: Optional[int] = 365
    
    @validator("name")
    def validate_name(cls, v):
        """Validate key name."""
        if len(v) < 3:
            raise ValueError("API key name must be at least 3 characters")
        return v
    
    @validator("scopes")
    def validate_scopes(cls, v):
        """Validate scopes."""
        valid_scopes = ["read", "write", "admin", "delete"]
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f"Invalid scope: {scope}")
        return v


class APIKeyManagementService:
    """
    API Key management service.
    
    Handles API key generation, validation, and lifecycle.
    """

    async def init_schema(self) -> None:
        """Initialize API key schema."""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS api_keys (
            id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            key_hash VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            scopes JSONB DEFAULT '[]'::jsonb,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            last_used TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        CREATE INDEX IF NOT EXISTS idx_api_keys_user ON api_keys(user_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
        CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(is_active);
        """
        
        await postgres_client.connect()
        await postgres_client.execute(schema_sql)
        logger.info("API key management schema initialized")

    def generate_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            API key in format: dcis_xxxxxxxxxxxxxxxxxxxxx
        """
        random_part = secrets.token_urlsafe(32)
        return f"dcis_{random_part}"

    def hash_key(self, api_key: str) -> str:
        """Hash an API key using SHA-256."""
        import hashlib
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def create_api_key(self, key_data: APIKeyCreate) -> tuple[str, APIKey]:
        """
        Create a new API key.
        
        Args:
            key_data: API key creation data
            
        Returns:
            Tuple of (plain_text_key, api_key_object)
            NOTE: Plain text key is returned only once!
        """
        # Generate key
        plain_key = self.generate_key()
        key_hash = self.hash_key(plain_key)
        key_id = f"key_{secrets.token_urlsafe(16)}"
        
        # Calculate expiration
        expires_at = None
        if key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
        
        # Insert into database
        await postgres_client.execute(
            """
            INSERT INTO api_keys 
            (id, user_id, key_hash, name, scopes, expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            key_id,
            key_data.user_id,
            key_hash,
            key_data.name,
            key_data.scopes,
            expires_at,
        )
        
        logger.info(f"Created API key: {key_data.name} for user {key_data.user_id}")
        
        api_key = APIKey(
            id=key_id,
            user_id=key_data.user_id,
            key_hash=key_hash,
            name=key_data.name,
            scopes=key_data.scopes,
            expires_at=expires_at,
        )
        
        return plain_key, api_key

    async def validate_api_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Args:
            api_key: Plain text API key
            
        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self.hash_key(api_key)
        
        row = await postgres_client.fetchrow(
            """
            SELECT * FROM api_keys 
            WHERE key_hash = $1 AND is_active = TRUE
            """,
            key_hash,
        )
        
        if not row:
            logger.warning("Invalid API key attempted")
            return None
        
        # Check expiration
        if row["expires_at"] and row["expires_at"] < datetime.utcnow():
            logger.warning(f"Expired API key used: {row['name']}")
            return None
        
        # Update usage stats
        await postgres_client.execute(
            """
            UPDATE api_keys 
            SET last_used = $1, usage_count = usage_count + 1
            WHERE id = $2
            """,
            datetime.utcnow(),
            row["id"],
        )
        
        return APIKey(
            id=row["id"],
            user_id=row["user_id"],
            key_hash=row["key_hash"],
            name=row["name"],
            scopes=row["scopes"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            last_used=datetime.utcnow(),
            usage_count=row["usage_count"] + 1,
        )

    async def revoke_api_key(self, key_id: str) -> bool:
        """Revoke an API key."""
        result = await postgres_client.execute(
            "UPDATE api_keys SET is_active = FALSE WHERE id = $1",
            key_id,
        )
        
        logger.info(f"Revoked API key: {key_id}")
        return "UPDATE" in result

    async def list_user_api_keys(
        self,
        user_id: str,
        include_inactive: bool = False,
    ) -> List[APIKey]:
        """List all API keys for a user."""
        query = "SELECT * FROM api_keys WHERE user_id = $1"
        
        if not include_inactive:
            query += " AND is_active = TRUE"
        
        query += " ORDER BY created_at DESC"
        
        rows = await postgres_client.fetch(query, user_id)
        
        return [
            APIKey(
                id=row["id"],
                user_id=row["user_id"],
                key_hash=row["key_hash"],
                name=row["name"],
                scopes=row["scopes"],
                is_active=row["is_active"],
                created_at=row["created_at"],
                expires_at=row["expires_at"],
                last_used=row["last_used"],
                usage_count=row["usage_count"],
            )
            for row in rows
        ]

    async def get_api_key_stats(self, key_id: str) -> Optional[Dict]:
        """Get usage statistics for an API key."""
        row = await postgres_client.fetchrow(
            "SELECT * FROM api_keys WHERE id = $1",
            key_id,
        )
        
        if not row:
            return None
        
        return {
            "name": row["name"],
            "usage_count": row["usage_count"],
            "last_used": row["last_used"],
            "created_at": row["created_at"],
            "expires_at": row["expires_at"],
            "is_active": row["is_active"],
            "scopes": row["scopes"],
        }

    async def rotate_api_key(self, key_id: str) -> tuple[str, APIKey]:
        """
        Rotate an API key (revoke old, create new).
        
        Args:
            key_id: ID of key to rotate
            
        Returns:
            New plain text key and APIKey object
        """
        # Get old key
        old_key_row = await postgres_client.fetchrow(
            "SELECT * FROM api_keys WHERE id = $1",
            key_id,
        )
        
        if not old_key_row:
            raise ValueError(f"API key not found: {key_id}")
        
        # Revoke old key
        await self.revoke_api_key(key_id)
        
        # Create new key with same properties
        new_key_data = APIKeyCreate(
            user_id=old_key_row["user_id"],
            name=f"{old_key_row['name']} (rotated)",
            scopes=old_key_row["scopes"],
        )
        
        plain_key, new_api_key = await self.create_api_key(new_key_data)
        
        logger.info(f"Rotated API key: {key_id} -> {new_api_key.id}")
        
        return plain_key, new_api_key


# Global instance
api_key_service = APIKeyManagementService()
