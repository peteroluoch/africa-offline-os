"""
Community Module - Infrastructure-First Social Distribution Layer.

This module treats Community Groups as the primary account holders,
enabling trusted local organizations to publish events and announcements
while individuals inquire without friction.

Design Principles:
- Groups hold accounts, not individuals
- Zero individual authentication required
- Inquiry-first model with caching
- Offline-first, edge-native
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional, Tuple

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
    """
    Core domain logic for the Community Distribution Layer.
    
    Exposes a strict interface for group management, event scheduling,
    announcement broadcasting, and inquiry handling.
    """

    def __init__(self, dispatcher: EventDispatcher, connection: sqlite3.Connection):
        self._dispatcher = dispatcher
        self._groups = CommunityGroupRepository(connection)
        self._events = CommunityEventRepository(connection)
        self._announcements = CommunityAnnouncementRepository(connection)
        self._inquiries = CommunityInquiryRepository(connection)

    # --- Group Management ---

    async def register_group(
        self,
        name: str,
        tags: List[str],
        location: str,
        admin_id: str,
        preferred_channels: str = "ussd,sms",
        group_type: str = "",
        description: str = ""
    ) -> CommunityGroupDTO:
        """
        Register a new community group.
        
        Args:
            name: Group name
            tags: Free-text tags (e.g., ["church"], ["mosque"], ["sacco"])
            location: Geographic location or identifier
            admin_id: Operator ID responsible for this group
            preferred_channels: Comma-separated list of channels
            group_type: Optional type descriptor
            description: Optional description
            
        Returns:
            Newly created CommunityGroupDTO
        """
        group = CommunityGroupDTO(
            id=f"GRP-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            description=description,
            group_type=group_type,
            tags=json.dumps(tags),
            location=location,
            admin_id=admin_id,
            trust_level="local",
            preferred_channels=preferred_channels,
            active=True
        )
        self._groups.save(group)
        
        await self._dispatcher.dispatch("COMMUNITY_GROUP_REGISTERED", {
            "id": group.id,
            "name": name,
            "location": location,
            "tags": tags
        })
        
        return group

    def get_group(self, group_id: str) -> Optional[CommunityGroupDTO]:
        """Retrieve a group by ID."""
        return self._groups.get_by_id(group_id)

    def list_groups(self) -> List[CommunityGroupDTO]:
        """List all registered groups."""
        return self._groups.list_all()

    def discover_groups(
        self,
        location: Optional[str] = None,
        tag_filter: Optional[List[str]] = None
    ) -> List[CommunityGroupDTO]:
        """
        Discover groups by location and/or tags.
        
        Args:
            location: Filter by location (substring match)
            tag_filter: Filter by tags (any match)
            
        Returns:
            List of matching groups
        """
        all_groups = self._groups.list_all()
        results = []
        
        for group in all_groups:
            if not group.active:
                continue
                
            # Location filter
            if location and group.location:
                if location.lower() not in group.location.lower():
                    continue
            
            # Tag filter
            if tag_filter:
                group_tags = json.loads(group.tags)
                if not any(tag.lower() in [t.lower() for t in group_tags] for tag in tag_filter):
                    continue
            
            results.append(group)
        
        return results

    # --- Event Management ---

    async def publish_event(
        self,
        group_id: str,
        title: str,
        event_type: str,
        start_time: datetime,
        language: str = "en",
        end_time: Optional[datetime] = None,
        recurrence: Optional[str] = None,
        visibility: str = "public"
    ) -> CommunityEventDTO:
        """
        Publish a new event for a group.
        
        Args:
            group_id: Group ID
            title: Event title
            event_type: Free-text event type
            start_time: Event start time
            language: Language code (default: en)
            end_time: Optional end time
            recurrence: Optional recurrence pattern
            visibility: public or members
            
        Returns:
            Newly created CommunityEventDTO
        """
        event = CommunityEventDTO(
            id=f"EVT-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            title=title,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            recurrence=recurrence,
            visibility=visibility,
            language=language
        )
        self._events.save(event)
        
        await self._dispatcher.dispatch("COMMUNITY_EVENT_PUBLISHED", {
            "id": event.id,
            "group_id": group_id,
            "title": title,
            "start_time": start_time.isoformat()
        })
        
        return event

    def list_events(
        self,
        location: Optional[str] = None,
        date: Optional[datetime] = None
    ) -> List[CommunityEventDTO]:
        """
        List events, optionally filtered by location and/or date.
        
        Args:
            location: Filter by group location
            date: Filter by event date
            
        Returns:
            List of matching events
        """
        all_events = self._events.list_all()
        
        if not location and not date:
            return all_events
        
        results = []
        for event in all_events:
            # Location filter (requires group lookup)
            if location:
                group = self._groups.get_by_id(event.group_id)
                if not group or not group.location or location.lower() not in group.location.lower():
                    continue
            
            # Date filter
            if date:
                if event.start_time.date() != date.date():
                    continue
            
            results.append(event)
        
        return results

    # --- Announcements & Broadcasts ---

    async def publish_announcement(
        self,
        group_id: str,
        message: str,
        urgency: str = "normal",
        expires_at: Optional[datetime] = None,
        target_audience: str = "public"
    ) -> CommunityAnnouncementDTO:
        """
        Publish an announcement for a group.
        
        Args:
            group_id: Group ID
            message: Announcement message
            urgency: normal or urgent
            expires_at: Optional expiry timestamp
            target_audience: public or members
            
        Returns:
            Newly created CommunityAnnouncementDTO
        """
        announcement = CommunityAnnouncementDTO(
            id=f"ANN-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            message=message,
            urgency=urgency,
            expires_at=expires_at,
            target_audience=target_audience
        )
        self._announcements.save(announcement)
        
        await self._dispatcher.dispatch("COMMUNITY_ANNOUNCEMENT_CREATED", {
            "id": announcement.id,
            "group_id": group_id,
            "message": message,
            "urgency": urgency
        })
        
        return announcement

    # --- Inquiry Handling ---

    async def handle_inquiry(
        self,
        group_id: str,
        question: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Handle an inquiry using the cache.
        
        Args:
            group_id: Group ID
            question: User's question
            
        Returns:
            Tuple of (answer, inquiry_id) if found, else (None, None)
        """
        normalized = question.strip().lower()
        
        all_inquiries = self._inquiries.list_all()
        for inquiry in all_inquiries:
            if inquiry.group_id != group_id:
                continue
            
            if inquiry.normalized_question in normalized or normalized in inquiry.normalized_question:
                # Increment hit count
                inquiry.hit_count += 1
                self._inquiries.save(inquiry)
                
                return (inquiry.answer, inquiry.id)
        
        return (None, None)

    async def reply_to_inquiry(
        self,
        inquiry_id: str,
        response: str
    ) -> None:
        """
        Reply to an inquiry by updating or creating a cache entry.
        
        Args:
            inquiry_id: Inquiry ID (if updating existing)
            response: Admin's response
        """
        inquiry = self._inquiries.get_by_id(inquiry_id)
        if inquiry:
            inquiry.answer = response
            inquiry.last_updated = datetime.utcnow()
            self._inquiries.save(inquiry)

    async def add_cached_inquiry(
        self,
        group_id: str,
        normalized_question: str,
        answer: str
    ) -> CommunityInquiryDTO:
        """
        Add a new cached inquiry response.
        
        Args:
            group_id: Group ID
            normalized_question: Normalized question pattern
            answer: Cached answer
            
        Returns:
            Newly created CommunityInquiryDTO
        """
        inquiry = CommunityInquiryDTO(
            id=f"INQ-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            normalized_question=normalized_question.strip().lower(),
            answer=answer,
            hit_count=0
        )
        self._inquiries.save(inquiry)
        return inquiry
