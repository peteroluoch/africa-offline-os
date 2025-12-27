from __future__ import annotations

from aos.core.channels.base import ChannelRequest, ChannelResponse
from aos.db.models import HarvestDTO
from datetime import datetime
import uuid
import re


class AgriSMSHandler:
    """Command handler for the Agri vehicle."""

    def __init__(self, agri_module: 'AgriModule' | None = None):
        self.agri = agri_module

    async def process(self, request: ChannelRequest) -> ChannelResponse:
        text = request.content.strip().upper()

        if text.startswith("HARVEST"):
            # Regex: HARVEST [CROP] [QTY] [GRADE]
            match = re.match(r"HARVEST\s+(\w+)\s+([\d.]+)\s+(\w+)", text)
            if not match:
                return ChannelResponse("Invalid format. Use: HARVEST [CROP] [QTY] [GRADE]")

            crop, qty, grade = match.groups()
            qty = float(qty)

            if self.agri:
                harvest = HarvestDTO(
                    id=f"H-{uuid.uuid4().hex[:8].upper()}",
                    farmer_id=request.sender,
                    crop_id=crop,
                    quantity=qty,
                    unit="BAGS",
                    quality_grade=grade,
                    harvest_date=datetime.now()
                )
                await self.agri.record_harvest(harvest)
                return ChannelResponse(f"✓ Harvest recorded: {qty} bags Grade {grade} {crop}. Ref: {harvest.id}")

            return ChannelResponse(f"✓ SMS Harvest parsed: {qty} bags Grade {grade} {crop}")

        return ChannelResponse("Unknown Agri command. Use HARVEST [CROP] [QTY] [GRADE]")
