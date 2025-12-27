from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from aos.db.models import (
    CommunityGroupDTO, 
    CommunityEventDTO, 
    CommunityAnnouncementDTO,
    CommunityInquiryDTO
)
from aos.db.repository import (
    CommunityGroupRepository,
    CommunityEventRepository,
    CommunityAnnouncementRepository,
    CommunityInquiryRepository
)

if TYPE_CHECKING:
    from aos.bus.dispatcher import EventDispatcher

class CommunityModule:
    """Core logic for the Community Distribution Layer."""

    def __init__(self, dispatcher: EventDispatcher, connection: sqlite3.Connection):
        self._dispatcher = dispatcher
        self._groups = CommunityGroupRepository(connection)
        self._events = CommunityEventRepository(connection)
        self._announcements = CommunityAnnouncementRepository(connection)
        self._inquiries = CommunityInquiryRepository(connection)

    # --- Group Management ---

    async def register_group(self, name: str, group_type: str, admin_id: str, description: str = "") -> CommunityGroupDTO:
        group = CommunityGroupDTO(
            id=f"GRP-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            group_type=group_type,
            admin_id=admin_id,
            trust_level="local"
        )
        self._groups.save(group)
        # TODO: Dispatch EVENT_COMMUNITY_GROUP_REGISTERED
        return group

    def get_group(self, group_id: str) -> Optional[CommunityGroupDTO]:
        return self._groups.get_by_id(group_id)

    def list_groups(self) -> List[CommunityGroupDTO]:
        return self._groups.list_all()

    # --- Event Management ---

    async def schedule_event(self, group_id: str, title: str, start_time: datetime, event_type: str = "general") -> CommunityEventDTO:
        event = CommunityEventDTO(
            id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            title=title,
            event_type=event_type,
            start_time=start_time
        )
        self._events.save(event)
        return event

    def list_events(self, group_id: str) -> List[CommunityEventDTO]:
        # Simple filtering for demo, normally would be a repo query
        all_events = self._events.list_all()
        return [e for e in all_events if e.group_id == group_id]

    # --- Announcements & Broadcasts ---

    async def create_announcement(self, group_id: str, message: str, urgency: str = "normal") -> CommunityAnnouncementDTO:
        announcement = CommunityAnnouncementDTO(
            id=f"ANN-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            message=message,
            urgency=urgency
        )
        self._announcements.save(announcement)
        
        # Dispatch for adapters to pick up
        await self._dispatcher.dispatch("COMMUNITY_ANNOUNCEMENT_CREATED", {
            "id": announcement.id,
            "group_id": group_id,
            "message": message,
            "urgency": urgency
        })
        return announcement

    # --- Inquiry Handling ---

    async def handle_inquiry(self, group_id: str, query: str) -> Optional[str]:
        """Attempt to answer an inquiry using the cache."""
        all_inquiries = self._inquiries.list_all()
        for inquiry in all_inquiries:
            if inquiry.group_id == group_id and inquiry.question_pattern.upper() in query.upper():
                return inquiry.cached_response
        return None

    async def add_cached_inquiry(self, group_id: str, pattern: str, response: str):
        inquiry = CommunityInquiryDTO(
            id=f"INQ-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            question_pattern=pattern,
            cached_response=response
        )
        self._inquiries.save(inquiry)
