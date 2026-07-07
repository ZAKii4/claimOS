from typing import Dict, Any
from app.integration.connectors.base import Connector


class BaseConnector(Connector):
    def __init__(self, cid: str, name: str):
        self._id = cid
        self._name = name
        self.connected = False
        self.authenticated = False

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def connect(self) -> bool:
        self.connected = True
        return True

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        self.authenticated = True
        return True

    def send(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent", "endpoint": endpoint, "payload": payload}

    def receive(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        return {"status": "received", "data": []}

    def health_check(self) -> bool:
        return self.connected


class CRMConnector(BaseConnector):
    def __init__(self):
        super().__init__("crm_01", "Salesforce CRM Connector")


class ERPConnector(BaseConnector):
    def __init__(self):
        super().__init__("erp_01", "SAP ERP Connector")


class RESTConnector(BaseConnector):
    def __init__(self):
        super().__init__("rest_01", "Generic REST API Connector")
        
    def send(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate an HTTP request
        return {"status": 200, "data": payload}
