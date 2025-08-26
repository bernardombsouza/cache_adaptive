from pydantic import BaseModel
from typing import Optional
from datetime import timedelta, datetime
import time

class CachePolicy(BaseModel):
    creation_time: Optional[datetime] = None
    last_access_time: Optional[datetime] = None
    ttl:timedelta = None
    tti:timedelta = None

    def with_ttl(self, ttl: timedelta) -> 'CachePolicy':
        self.creation_time = datetime.now()
        self.ttl = ttl
        return self
    
    def with_tti(self, tti: timedelta) -> 'CachePolicy':
        self.last_access_time = datetime.now()
        self.tti = tti
        return self
    
    def expired(ttl, tti, creation_time, last_access_time) -> bool:
        now = datetime.now()
        if ttl and creation_time:
            if now - creation_time > ttl:
                return True
        if tti and last_access_time:
            if now - last_access_time > tti:
                return True
        return False

print(CachePolicy().with_ttl(timedelta(seconds=10)).with_tti(timedelta(seconds=5)))
