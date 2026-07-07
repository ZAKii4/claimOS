from typing import Dict, List, Optional
from app.governance.models import User, Role, Permission


class RBACEngine:
    """Role-Based Access Control engine."""

    _roles: Dict[str, Role] = {}
    _users: Dict[str, User] = {}

    @classmethod
    def register_role(cls, role: Role):
        cls._roles[role.name] = role

    @classmethod
    def register_user(cls, user: User):
        cls._users[user.id] = user

    @classmethod
    def get_user(cls, user_id: str) -> Optional[User]:
        return cls._users.get(user_id)

    @classmethod
    def get_all_users(cls) -> List[User]:
        return list(cls._users.values())

    @classmethod
    def get_all_roles(cls) -> List[Role]:
        return list(cls._roles.values())

    @classmethod
    def has_permission(cls, user_id: str, resource: str, action: str) -> bool:
        """Check if a user has a specific permission via their roles."""
        user = cls._users.get(user_id)
        if not user or not user.active:
            return False

        required = Permission(resource=resource, action=action)

        for role_name in user.roles:
            role = cls._roles.get(role_name)
            if role and required in role.permissions:
                return True

        return False
