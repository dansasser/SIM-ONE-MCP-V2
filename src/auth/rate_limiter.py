"""
Rate limiting module for API key usage.
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
import threading


class RateLimiter:
    """
    Simple in-memory rate limiter.
    Tracks requests per API key hash.
    """
    
    def __init__(self, max_requests: int = 1000, window_hours: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_hours: Time window in hours
        """
        self.max_requests = max_requests
        self.window_hours = window_hours
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.lock = threading.Lock()
    
    def check_rate_limit(self, key_hash: str) -> bool:
        """
        Check if a request is allowed for the given key hash.
        
        Args:
            key_hash: The hashed API key
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(hours=self.window_hours)
            
            # Get requests for this key
            key_requests = self.requests[key_hash]
            
            # Remove old requests outside the window
            key_requests[:] = [req_time for req_time in key_requests if req_time > cutoff]
            
            # Check if limit exceeded
            if len(key_requests) >= self.max_requests:
                return False
            
            # Add this request
            key_requests.append(now)
            
            return True
    
    def get_usage(self, key_hash: str) -> int:
        """Get current usage count for a key."""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(hours=self.window_hours)
            
            key_requests = self.requests[key_hash]
            key_requests[:] = [req_time for req_time in key_requests if req_time > cutoff]
            
            return len(key_requests)
    
    def reset_key(self, key_hash: str) -> None:
        """Reset rate limit for a specific key."""
        with self.lock:
            if key_hash in self.requests:
                del self.requests[key_hash]


# Global rate limiter instance
_rate_limiter = RateLimiter(max_requests=1000, window_hours=1)


def check_rate_limit(key_hash: str) -> bool:
    """Check if request is allowed for the given key hash."""
    return _rate_limiter.check_rate_limit(key_hash)


def get_usage(key_hash: str) -> int:
    """Get current usage count for a key."""
    return _rate_limiter.get_usage(key_hash)


def reset_key(key_hash: str) -> None:
    """Reset rate limit for a specific key."""
    _rate_limiter.reset_key(key_hash)

