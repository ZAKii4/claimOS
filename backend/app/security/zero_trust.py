import uuid
from typing import Dict, Any, List

class ZeroTrustEngine:
    """
    Calculates risk scores based on anomalies (IP, Device, Travel).
    """
    def __init__(self):
        # Mock database of known devices per user
        self.known_devices = {}
        
    def calculate_risk_score(self, user_id: str, ip_address: str, device_id: str) -> int:
        """
        Returns a risk score from 0 (Safe) to 100 (High Risk).
        """
        score = 0
        user_devices = self.known_devices.get(user_id, [])
        
        # New device adds risk
        if device_id not in user_devices:
            score += 40
            
        # Here we would normally check GeoIP for impossible travel
        # Mock: if IP starts with "192.168", it's safe local. If "unknown", it's high risk.
        if ip_address == "unknown":
            score += 50
            
        return min(score, 100)
        
    def register_device(self, user_id: str, device_id: str):
        if user_id not in self.known_devices:
            self.known_devices[user_id] = []
        if device_id not in self.known_devices[user_id]:
            self.known_devices[user_id].append(device_id)

zero_trust_engine = ZeroTrustEngine()
