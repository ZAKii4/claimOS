from typing import Dict, Any
from app.governance.models import User


class ABACEngine:
    """Attribute-Based Access Control engine."""

    @classmethod
    def evaluate(cls, user: User, resource_attrs: Dict[str, Any], action: str) -> bool:
        """
        Evaluate access based on user attributes and resource attributes.

        Examples of policies encoded here:
        - A user with department="fraud" can access fraud resources
        - A user with clearance_level >= resource's required_level can access
        """
        if not user.active:
            return False

        # Check department match
        user_dept = user.attributes.get("department", "")
        resource_dept = resource_attrs.get("department", "")
        if resource_dept and user_dept != resource_dept:
            return False

        # Check clearance level
        user_level = user.attributes.get("clearance_level", 0)
        required_level = resource_attrs.get("required_level", 0)
        if user_level < required_level:
            return False

        return True
