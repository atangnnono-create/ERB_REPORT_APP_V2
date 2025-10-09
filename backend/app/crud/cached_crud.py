from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.core.cache import cache_service
from backend.app.crud import crud
from backend.app.models import models
from backend.app.schemas import schemas
import logging

logger = logging.getLogger(__name__)


class CachedCRUD:
    def __init__(self):
        self.cache = cache_service

    def get_user(self, db: Session, user_id: int) -> Optional[models.User]:
        """Get user with cache"""
        cache_key = f"get_user:user_id:{user_id}"

        @self.cache.cached(ttl=300)  # Cache for 5 minutes
        def _get_user():
            return crud.get_user(db, user_id)

        return _get_user()

    def get_user_by_email(self, db: Session, email: str) -> Optional[models.User]:
        """Get user by email with cache"""
        cache_key = f"get_user_by_email:email:{email}"

        @self.cache.cached(ttl=300)
        def _get_user_by_email():
            return crud.get_user_by_email(db, email)

        return _get_user_by_email()

    def get_reports(self, db: Session, user_id: int) -> List[models.Report]:
        """Get user's reports with cache"""
        cache_key = f"get_reports:user_id:{user_id}"

        @self.cache.cached(ttl=60)  # Cache for 1 minute
        def _get_reports():
            return crud.get_reports(db, user_id)

        return _get_reports()

    def get_report(self, db: Session, report_id: int, user_id: int) -> Optional[models.Report]:
        """Get single report with cache"""
        cache_key = f"get_report:report_id:{report_id}:user_id:{user_id}"

        @self.cache.cached(ttl=60)
        def _get_report():
            return crud.get_report(db, report_id, user_id)

        return _get_report()

    def invalidate_user_cache(self, user_id: int):
        """Invalidate all cache entries for a user"""
        self.cache.invalidate_user_data(user_id)

    def invalidate_report_cache(self, report_id: int, user_id: int):
        """Invalidate cache for specific report"""
        patterns = [
            f"app:get_report:*:report_id:{report_id}:*",
            f"app:get_reports:*:user_id:{user_id}:*"
        ]
        for pattern in patterns:
            self.cache.invalidate_pattern(pattern)


# Global cached CRUD instance
cached_crud = CachedCRUD()