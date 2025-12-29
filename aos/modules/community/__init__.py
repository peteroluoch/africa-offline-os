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
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from aos.bus.events import Event
from aos.db.models import (
    CommunityAnnouncementDTO,
    CommunityEventDTO,
    CommunityGroupDTO,
    CommunityInquiryDTO,
    CommunityMemberDTO,
)
from aos.db.repository import (
    CommunityAnnouncementRepository,
    CommunityEventRepository,
    CommunityGroupRepository,
    CommunityInquiryRepository,
)

from .broadcast import BroadcastManager, BroadcastWorker

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
        self._db = connection  # SECURITY: Direct DB access for member queries
        self._groups = CommunityGroupRepository(connection)
        self._events = CommunityEventRepository(connection)
        self._announcements = CommunityAnnouncementRepository(connection)
        self._inquiries = CommunityInquiryRepository(connection)
        self._broadcasts = BroadcastManager(connection)
        self._worker = BroadcastWorker(self._broadcasts, dispatcher)

    async def initialize(self):
        """Initialize the module and start background workers."""
        self._worker.start()

    async def shutdown(self):
        """Gracefully stop background workers."""
        await self._worker.stop()

    def _log_activity(
        self,
        actor_id: str,
        action: str,
        target_id: str,
        community_id: str | None = None,
        metadata: dict | None = None
    ):
        """Internal helper to record audit logs."""
        log_id = f"LOG-{uuid.uuid4().hex[:8].upper()}"
        self._db.execute("""
            INSERT INTO community_activity_logs (id, actor_id, action, target_id, community_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, actor_id, action, target_id, community_id, json.dumps(metadata) if metadata else None))
        self._db.commit()

    # --- Group Management ---

    async def register_group(
        self,
        name: str,
        tags: list[str],
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
            Newly created or existing CommunityGroupDTO
        """
        # FAANG: Idempotency check to prevent duplicate groups by name in the same location
        existing = self._groups.list_all()
        for g in existing:
            if g.name == name and g.location == location:
                return g

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

        await self._dispatcher.dispatch(Event(
            name="COMMUNITY_GROUP_REGISTERED",
            payload={
                "id": group.id,
                "name": name,
                "location": location,
                "tags": tags
            }
        ))

        return group

    async def deactivate_group(self, group_id: str, admin_id: str) -> bool:
        """
        Soft-delete (deactivate) a community group.
        
        SECURITY: Must be root or the group's admin.
        """
        group = self.get_group(group_id)
        if not group:
            return False

        group.active = False
        self._groups.save(group)

        await self._dispatcher.dispatch(Event(
            name="COMMUNITY_GROUP_DEACTIVATED",
            payload={
                "id": group_id,
                "admin_id": admin_id
            }
        ))
        return True

    def get_group(self, group_id: str) -> CommunityGroupDTO | None:
        """Retrieve a group by ID."""
        return self._groups.get_by_id(group_id)

    def list_groups(
        self,
        page: int = 1,
        per_page: int = 10,
        search_query: str | None = None,
        group_type: str | None = None,
        trust_level: str | None = None
    ) -> dict:
        """List registered groups with filtering and pagination.
        
        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search_query: Search in name, description, or location
            group_type: Filter by group type (tag)
            trust_level: Filter by trust status
            
        Returns:
            Dict with 'groups', 'total', 'page', 'per_page', 'total_pages'
        """
        # Get all groups
        groups = [g for g in self._groups.list_all() if g.active]

        # Apply filters
        if search_query:
            q = search_query.lower()
            groups = [
                g for g in groups
                if q in g.name.lower() or
                   (g.description and q in g.description.lower()) or
                   q in g.location.lower()
            ]

        if group_type:
            # We treat the first tag or the explicit group_type field as the type
            groups = [g for g in groups if g.group_type == group_type]

        if trust_level:
            groups = [g for g in groups if g.trust_level == trust_level]

        total = len(groups)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 0

        # Validate page number
        page = max(1, min(page, total_pages if total_pages > 0 else 1))

        # Calculate slice
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page

        return {
            "groups": groups[start_idx:end_idx],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    def get_group_types(self) -> list[str]:
        """Get unique active group types for filter dropdowns."""
        groups = self._groups.list_all()
        types = set()
        for g in groups:
            if g.active and g.group_type:
                types.add(g.group_type)
        return sorted(list(types))

    def discover_groups(
        self,
        location: str | None = None,
        tag_filter: list[str] | None = None
    ) -> list[CommunityGroupDTO]:
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
        end_time: datetime | None = None,
        recurrence: str | None = None,
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

        await self._dispatcher.dispatch(Event(
            name="COMMUNITY_EVENT_PUBLISHED",
            payload={
                "id": event.id,
                "group_id": group_id,
                "title": title,
                "start_time": start_time.isoformat()
            }
        ))

        return event

    def list_events(
        self,
        location: str | None = None,
        date: datetime | None = None
    ) -> list[CommunityEventDTO]:
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
        expires_at: datetime | None = None,
        target_audience: str = "public",
        actor_id: str = "system",
        cost_confirmed: bool = False,
        cost_threshold_kes: float = 100.0
    ) -> CommunityAnnouncementDTO:
        """
        Publish an announcement for a group.
        
        SECURITY: Enforces admin->community isolation.
        
        Args:
            group_id: Group ID
            message: Announcement message
            urgency: normal or urgent
            expires_at: Optional expiry timestamp
            target_audience: public or members
            actor_id: ID of the user publishing (must be group admin)
            
        Returns:
            Newly created CommunityAnnouncementDTO
        """
        # 0. Security Check
        group = self._groups.get_by_id(group_id)
        if not group:
            raise ValueError(f"Invalid community: {group_id}")
            
        if actor_id != "system" and group.admin_id != actor_id:
            # We allow "system" for automated messages, but human actors must match
             raise ValueError(f"Admin {actor_id} not authorized for community {group.id}")

        # 0.5 COST GUARDRAIL (FAANG MANDATORY)
        # Calculate estimated cost BEFORE queuing
        recipient_count = len(self.get_community_members(group_id))
        
        # Cost calculation (KES per SMS, conservative estimate)
        # SMS: ~0.80 KES, USSD: ~0.50 KES per session
        # We use SMS as worst-case
        estimated_cost_kes = recipient_count * 0.80
        
        # Require explicit confirmation for large sends
        if estimated_cost_kes > cost_threshold_kes and not cost_confirmed:
            raise ValueError(
                f"COST_CONFIRMATION_REQUIRED|" 
                f"Estimated cost: KES {estimated_cost_kes:.2f}|" 
                f"Recipients: {recipient_count}|" 
                f"Channels: SMS, USSD|" 
                f"Message length: {len(message)} chars"
            )

        # 1. Create the domain announcement record (Audit Persistence)
        announcement = CommunityAnnouncementDTO(
            id=f"ANN-{uuid.uuid4().hex[:8].upper()}",
            group_id=group_id,
            message=message,
            urgency=urgency,
            expires_at=expires_at,
            target_audience=target_audience
        )
        self._announcements.save(announcement)

        # 2. Queue the resilient broadcast (FAANG-grade Resilience)
        # We use the announcement ID as the idempotency key to prevent double-queuing
        broadcast_id = self._broadcasts.create_broadcast(
            community_id=group_id,
            message=message,
            channels=["sms", "ussd"], # Default channels for community
            actor_id=actor_id, 
            idempotency_key=announcement.id
        )

        # 3. Mark for auto-approval/queueing for immediate processing
        self._broadcasts.approve_broadcast(broadcast_id, actor_id)
        self._broadcasts.queue_broadcast(broadcast_id, actor_id)

        # 4. Dispatch the creation event (for real-time dashboard updates)
        await self._dispatcher.dispatch(Event(
            name="COMMUNITY_ANNOUNCEMENT_CREATED",
            payload={
                "id": announcement.id,
                "broadcast_id": broadcast_id,
                "group_id": group_id,
                "message": message,
                "urgency": urgency
            }
        ))

        return announcement

    # --- Member Management (SECURITY-CRITICAL) ---

    def add_member_to_community(
        self,
        community_id: str,
        user_id: str,
        channel: str,
        actor_id: str = "system"
    ) -> bool:
        """
        Add a user to a community.
        
        SECURITY: This is the ONLY way to associate users with communities.
        
        Args:
            community_id: Community ID (REQUIRED)
            user_id: User identifier (phone, chat_id, etc.)
            channel: Channel type ('telegram', 'sms', 'ussd', 'whatsapp')
            
        Returns:
            True if added successfully
            
        Raises:
            ValueError: If any required parameter is missing or invalid
        """
        if not community_id or not user_id or not channel:
            raise ValueError("community_id, user_id, and channel are required")

        # Verify community exists
        if not self._groups.get_by_id(community_id):
            raise ValueError(f"Invalid community_id: {community_id}")

        member_id = f"MEM-{uuid.uuid4().hex[:8].upper()}"
        self._db.execute("""
            INSERT OR IGNORE INTO community_members 
            (id, community_id, user_id, channel, active)
            VALUES (?, ?, ?, ?, 1)
        """, (member_id, community_id, user_id, channel))
        self._db.commit()

        self._log_activity(
            actor_id=actor_id,
            action="member_add",
            target_id=member_id,
            community_id=community_id,
            metadata={"user_id": user_id, "channel": channel}
        )
        return True

    def remove_member_from_community(
        self,
        community_id: str,
        user_id: str,
        channel: str,
        actor_id: str = "system"
    ) -> bool:
        """
        Remove a user from a community (soft delete).
        
        Args:
            community_id: Community ID
            user_id: User identifier
            channel: Channel type
            
        Returns:
            True if removed successfully
        """
        self._db.execute("""
            UPDATE community_members 
            SET active = 0 
            WHERE community_id = ? AND user_id = ? AND channel = ?
        """, (community_id, user_id, channel))
        self._db.commit()

        self._log_activity(
            actor_id=actor_id,
            action="member_remove",
            target_id=f"{community_id}:{user_id}",
            community_id=community_id,
            metadata={"user_id": user_id, "channel": channel}
        )
        return True

    def update_community_member(
        self,
        member_id: str,
        user_id: str,
        channel: str,
        actor_id: str = "system"
    ) -> bool:
        """
        Update member details.
        
        Args:
            member_id: Internal member ID
            user_id: New user identifier
            channel: New channel type
            
        Returns:
            True if updated successfully
        """
        self._db.execute("""
            UPDATE community_members 
            SET user_id = ?, channel = ? 
            WHERE id = ?
        """, (user_id, channel, member_id))
        self._db.commit()

        self._log_activity(
            actor_id=actor_id,
            action="member_update",
            target_id=member_id,
            metadata={"user_id": user_id, "channel": channel}
        )
        return True

    def get_community_members(
        self,
        community_id: str,
        channel: str | None = None
    ) -> list[str]:
        """
        Resolve members of a community.
        
        SECURITY: This is the ONLY method that resolves recipients.
        MUST enforce WHERE community_id = ?
        
        Args:
            community_id: Community ID (REQUIRED)
            channel: Optional channel filter
            
        Returns:
            List of user IDs (phone numbers or chat IDs)
            
        Raises:
            ValueError: If community_id is None or invalid
        """
        if not community_id:
            raise ValueError("community_id is required for recipient resolution")

        # Verify community exists
        community = self._groups.get_by_id(community_id)
        if not community:
            raise ValueError(f"Invalid community_id: {community_id}")

        # KERNEL-LEVEL QUERY: Mandatory WHERE community_id = ?
        query = "SELECT user_id FROM community_members WHERE community_id = ? AND active = 1"
        params = [community_id]

        if channel:
            query += " AND channel = ?"
            params.append(channel)

        cursor = self._db.execute(query, params)
        return [row[0] for row in cursor.fetchall()]

    def list_all_members(
        self,
        page: int = 1,
        per_page: int = 50,
        group_id: str | None = None,
        channel: str | None = None,
        search_query: str | None = None
    ) -> dict:
        """
        List all community members with filtering and pagination.
        
        Args:
            page: Page number
            per_page: Items per page
            group_id: Filter by community
            channel: Filter by channel
            search_query: Search by user_id
            
        Returns:
            Dict with members and pagination info
        """
        query = "SELECT m.user_id, m.channel, m.joined_at, m.active, g.name as group_name, m.community_id, m.id FROM community_members m JOIN community_groups g ON m.community_id = g.id WHERE m.active = 1"
        params = []

        if group_id:
            query += " AND m.community_id = ?"
            params.append(group_id)
        if channel:
            query += " AND m.channel = ?"
            params.append(channel)
        if search_query:
            search_pattern = f"%{search_query}%"
            # Deep search across User ID, Group Name
            query += " AND (m.user_id LIKE ? OR g.name LIKE ?)"
            params.extend([search_pattern, search_pattern])

            # Smart phone normalization for Kenyan numbers
            if search_query.startswith('0') and len(search_query) > 1:
                query = query[:-1] + " OR m.user_id LIKE ?)"
                params.append(f"%+254{search_query[1:]}%")

        # Get total count
        count_params = list(params)
        count_query = query.replace("m.user_id, m.channel, m.joined_at, m.active, g.name as group_name, m.community_id, m.id", "COUNT(*)")
        total = self._db.execute(count_query, count_params).fetchone()[0]

        total_pages = (total + per_page - 1) // per_page if total > 0 else 0
        page = max(1, min(page, total_pages if total_pages > 0 else 1))

        # Add pagination
        query += " ORDER BY m.joined_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])

        rows = self._db.execute(query, params).fetchall()

        members = []
        for row in rows:
            members.append({
                "user_id": row[0],
                "channel": row[1],
                "joined_at": row[2] if isinstance(row[2], datetime) else datetime.fromisoformat(row[2]) if row[2] else None,
                "active": row[3],
                "group_name": row[4],
                "community_id": row[5],
                "id": row[6]
            })

        return {
            "members": members,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }

    async def deliver_announcement(
        self,
        announcement_id: str,
        admin_id: str
    ) -> dict:
        """
        Deliver an announcement to community members.
        
        SECURITY: Enforces admin→community binding and recipient scoping.
        
        Args:
            announcement_id: Announcement ID
            admin_id: Admin making the delivery request
            
        Returns:
            {
                "delivered": int,
                "failed": int,
                "community_id": str,
                "recipients": List[str]
            }
            
        Raises:
            ValueError: If announcement invalid or admin not authorized
        """
        # 1. Get announcement
        announcement = self._announcements.get_by_id(announcement_id)
        if not announcement:
            raise ValueError(f"Invalid announcement_id: {announcement_id}")

        community_id = announcement.group_id

        # 2. Verify admin→community binding
        community = self._groups.get_by_id(community_id)
        if not community:
            raise ValueError(f"Invalid community: {community_id}")

        if community.admin_id != admin_id:
            raise ValueError(
                f"Admin {admin_id} not authorized for community {community_id}"
            )

        # 3. Resolve recipients (KERNEL-LEVEL SCOPING)
        recipients = self.get_community_members(community_id)

        if not recipients:
            return {
                "delivered": 0,
                "failed": 0,
                "community_id": community_id,
                "recipients": []
            }

        # 4. Emit delivery event (adapters listen and send)
        await self._dispatcher.dispatch(Event(
            name="COMMUNITY_MESSAGE_DELIVER",
            payload={
                "announcement_id": announcement_id,
                "community_id": community_id,
                "message": announcement.message,
                "recipients": recipients,  # Pre-scoped by kernel
                "urgency": announcement.urgency
            }
        ))

        return {
            "delivered": len(recipients),
            "failed": 0,
            "community_id": community_id,
            "recipients": recipients
        }

    # --- Inquiry Handling ---

    async def handle_inquiry(
        self,
        group_id: str,
        question: str
    ) -> tuple[str | None, str | None]:
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
