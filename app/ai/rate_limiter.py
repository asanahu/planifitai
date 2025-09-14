"""Sistema de rate limiting inteligente para OpenRouter."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RateLimitManager:
    """Gestor de rate limits para OpenRouter."""
    
    def __init__(self):
        self._last_request_time = 0
        self._min_interval = 2.0  # Mínimo 2 segundos entre requests
        self._daily_requests = 0
        self._daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self._max_daily_requests = 45  # Dejamos margen de los 50 límite
    
    def can_make_request(self) -> bool:
        """Verifica si se puede hacer un request."""
        now = datetime.now()
        
        # Resetear contador diario si es nuevo día
        if now >= self._daily_reset_time:
            self._daily_requests = 0
            self._daily_reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Verificar límite diario
        if self._daily_requests >= self._max_daily_requests:
            logger.warning(f"Rate limit diario alcanzado: {self._daily_requests}/{self._max_daily_requests}")
            return False
        
        # Verificar intervalo mínimo
        time_since_last = time.time() - self._last_request_time
        if time_since_last < self._min_interval:
            sleep_time = self._min_interval - time_since_last
            logger.info(f"Esperando {sleep_time:.2f}s para respetar rate limit")
            time.sleep(sleep_time)
        
        return True
    
    def record_request(self):
        """Registra que se hizo un request."""
        self._last_request_time = time.time()
        self._daily_requests += 1
        logger.info(f"Request registrado. Total hoy: {self._daily_requests}/{self._max_daily_requests}")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del rate limiter."""
        now = datetime.now()
        time_until_reset = (self._daily_reset_time - now).total_seconds()
        
        return {
            "daily_requests": self._daily_requests,
            "max_daily_requests": self._max_daily_requests,
            "time_until_reset_hours": time_until_reset / 3600,
            "can_make_request": self.can_make_request(),
            "last_request_ago_seconds": time.time() - self._last_request_time
        }


# Instancia global del rate limiter
_rate_limiter = RateLimitManager()


def get_rate_limiter() -> RateLimitManager:
    """Obtiene la instancia global del rate limiter."""
    return _rate_limiter


def check_rate_limit() -> bool:
    """Verifica si se puede hacer un request respetando rate limits."""
    return _rate_limiter.can_make_request()


def record_api_request():
    """Registra que se hizo un request a la API."""
    _rate_limiter.record_request()
