"""
User management for role assignments
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user-role assignments"""
    
    def __init__(self, storage_path: str = "data/users.json"):
        self.storage_path = Path(storage_path)
        self.users: Dict[str, Dict[str, Any]] = {}
        self._ensure_storage_dir()
        self._load_users()
    
    def _ensure_storage_dir(self):
        """Ensure storage directory exists"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._save_users()
    
    def _load_users(self):
        """Load users from storage"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r') as f:
                    self.users = json.load(f)
                logger.info(f"Loaded {len(self.users)} users from storage")
            else:
                # Initialize with default admin user
                self.users = {
                    "admin@msil.com": {
                        "username": "admin@msil.com",
                        "email": "admin@msil.com",
                        "roles": ["admin"],
                        "created_at": datetime.utcnow().isoformat()
                    }
                }
                self._save_users()
        except Exception as e:
            logger.error(f"Failed to load users: {e}")
            self.users = {}
    
    def _save_users(self):
        """Save users to storage"""
        try:
            with open(self.storage_path, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save users: {e}")
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return [
            {
                "username": username,
                "email": user_data.get("email", username),
                "roles": user_data.get("roles", []),
                "created_at": user_data.get("created_at")
            }
            for username, user_data in self.users.items()
        ]
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        user_data = self.users.get(username)
        if user_data:
            return {
                "username": username,
                "email": user_data.get("email", username),
                "roles": user_data.get("roles", []),
                "created_at": user_data.get("created_at")
            }
        return None
    
    def get_or_create_user(self, username: str, email: Optional[str] = None) -> Dict[str, Any]:
        """Get or create user"""
        if username not in self.users:
            self.users[username] = {
                "username": username,
                "email": email or username,
                "roles": ["user"],  # Default role
                "created_at": datetime.utcnow().isoformat()
            }
            self._save_users()
            logger.info(f"Created new user: {username}")
        
        return self.get_user(username)
    
    def get_user_roles(self, username: str) -> List[str]:
        """Get user's roles"""
        user_data = self.users.get(username)
        if user_data:
            return user_data.get("roles", [])
        return []
    
    def set_user_roles(self, username: str, roles: List[str]) -> bool:
        """Set user's roles"""
        if username not in self.users:
            # Auto-create user if doesn't exist
            self.get_or_create_user(username)
        
        self.users[username]["roles"] = roles
        self._save_users()
        logger.info(f"Updated roles for {username}: {roles}")
        return True
    
    def add_user_role(self, username: str, role: str) -> bool:
        """Add a role to user"""
        if username not in self.users:
            self.get_or_create_user(username)
        
        current_roles = self.users[username].get("roles", [])
        if role not in current_roles:
            current_roles.append(role)
            self.users[username]["roles"] = current_roles
            self._save_users()
            logger.info(f"Added role '{role}' to user {username}")
        return True
    
    def remove_user_role(self, username: str, role: str) -> bool:
        """Remove a role from user"""
        if username not in self.users:
            return False
        
        current_roles = self.users[username].get("roles", [])
        if role in current_roles:
            current_roles.remove(role)
            self.users[username]["roles"] = current_roles
            self._save_users()
            logger.info(f"Removed role '{role}' from user {username}")
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        if username in self.users:
            del self.users[username]
            self._save_users()
            logger.info(f"Deleted user: {username}")
            return True
        return False
    
    def get_users_by_role(self, role: str) -> List[Dict[str, Any]]:
        """Get all users with a specific role"""
        return [
            {
                "username": username,
                "email": user_data.get("email", username),
                "roles": user_data.get("roles", []),
                "created_at": user_data.get("created_at")
            }
            for username, user_data in self.users.items()
            if role in user_data.get("roles", [])
        ]


# Global instance
user_manager = UserManager()
