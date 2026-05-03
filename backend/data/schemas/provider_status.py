import asyncio
from typing import Optional, List, Dict, Any

class ProviderStatus:
    def __init__(self, provider_id: int, name: str, is_configured: bool):
        self.provider_id = provider_id
        self.name = name
        self.is_configured = is_configured
