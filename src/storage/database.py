"""
Database - Supabase Integration

Stores extracted data in Supabase (PostgreSQL).
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel
import httpx
from src.config import config


class Entity(BaseModel):
    """Discovered entity (website/business)"""
    id: Optional[str] = None
    url: str
    title: str
    source: str
    relevance_score: float = 0.0
    scraped_at: Optional[datetime] = None
    
class Contact(BaseModel):
    """Contact information"""
    id: Optional[str] = None
    entity_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

class SocialAccount(BaseModel):
    """Social media account"""
    id: Optional[str] = None
    entity_id: str
    platform: str
    username: str
    url: str


class Database:
    """
    Supabase database client.
    
    Tables:
    - entities: Discovered websites
    - contacts: Email, phone, address
    - social_accounts: Social media profiles
    - media: Downloaded images/videos
    """
    
    def __init__(self):
        self.url = config.database.supabase_url
        self.key = config.database.supabase_key
        self.client = httpx.AsyncClient(
            base_url=f"{self.url}/rest/v1",
            headers={
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            }
        ) if self.url and self.key else None
    
    def is_configured(self) -> bool:
        """Check if database is configured"""
        return self.client is not None
    
    async def save_entity(self, entity: Entity) -> Optional[str]:
        """Save discovered entity"""
        if not self.is_configured():
            return None
        
        data = entity.model_dump(exclude={"id"})
        data["scraped_at"] = datetime.utcnow().isoformat()
        
        response = await self.client.post("/entities", json=data)
        if response.status_code == 201:
            result = response.json()
            return result[0]["id"] if result else None
        return None
    
    async def save_contact(self, contact: Contact) -> Optional[str]:
        """Save contact information"""
        if not self.is_configured():
            return None
        
        data = contact.model_dump(exclude={"id"})
        response = await self.client.post("/contacts", json=data)
        if response.status_code == 201:
            result = response.json()
            return result[0]["id"] if result else None
        return None
    
    async def save_social(self, social: SocialAccount) -> Optional[str]:
        """Save social media account"""
        if not self.is_configured():
            return None
        
        data = social.model_dump(exclude={"id"})
        response = await self.client.post("/social_accounts", json=data)
        if response.status_code == 201:
            result = response.json()
            return result[0]["id"] if result else None
        return None
    
    async def get_entity(self, url: str) -> Optional[Entity]:
        """Get entity by URL"""
        if not self.is_configured():
            return None
        
        response = await self.client.get(
            "/entities",
            params={"url": f"eq.{url}"}
        )
        if response.status_code == 200:
            result = response.json()
            if result:
                return Entity(**result[0])
        return None
    
    async def close(self):
        """Close database connection"""
        if self.client:
            await self.client.aclose()
