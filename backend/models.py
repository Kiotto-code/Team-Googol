"""
Database models for the Lost & Found system.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
import json

@dataclass
class FoundItem:
    """Model for found items."""
    id: Optional[int] = None
    filename: str = ""
    description: str = ""
    image_embedding: List[float] = None
    description_embedding: Optional[List[float]] = None
    status: str = "available"
    claimed_at: Optional[datetime] = None
    claimed_by: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "description": self.description,
            "status": self.status,
            "claimed_at": self.claimed_at.isoformat() if self.claimed_at else None,
            "claimed_by": self.claimed_by,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "url": f"http://127.0.0.1:5000/uploads/{self.filename}",
            "can_claim": self.status == "available",
            "is_claimed": self.status == "claimed"
        }
    
    @classmethod
    def from_db_row(cls, row) -> 'FoundItem':
        """Create instance from database row."""
        return cls(
            id=row['id'],
            filename=row['filename'],
            description=row['description'] or "",
            image_embedding=json.loads(row['image_embedding']) if row['image_embedding'] else None,
            description_embedding=json.loads(row['description_embedding']) if row['description_embedding'] else None,
            status=row['status'],
            claimed_at=datetime.fromisoformat(row['claimed_at']) if row['claimed_at'] else None,
            claimed_by=row['claimed_by'],
            uploaded_at=datetime.fromisoformat(row['uploaded_at']) if row['uploaded_at'] else None,
            expires_at=datetime.fromisoformat(row['expires_at']) if row['expires_at'] else None,
        )

@dataclass
class SearchResult:
    """Model for search results."""
    item: FoundItem
    score: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        result = self.item.to_dict()
        result["score"] = self.score
        return result
