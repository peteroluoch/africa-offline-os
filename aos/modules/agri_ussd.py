from __future__ import annotations

from aos.core.channels.base import ChannelResponse
from aos.core.channels.ussd import USSDSession


class AgriUSSDHandler:
    """Menu flow handler for the Agri vehicle."""

    def __init__(self):
        self.crops = {"1": "Maize", "2": "Beans", "3": "Sorghum"}
        self.grades = {"1": "A", "2": "B", "3": "C"}

    def process(self, session: USSDSession, user_input: str) -> ChannelResponse:
        state = session.state
        user_input = user_input.strip()

        if state == "START":
            if not user_input:
                return ChannelResponse("[A-OS Agri]\n1. Record Harvest\n2. Status", True)
            if user_input == "1":
                session.update("SELECT_CROP")
                return ChannelResponse("Select Crop:\n1. Maize\n2. Beans\n3. Sorghum", True)
            return ChannelResponse("Invalid option.", False)

        if state == "SELECT_CROP":
            if user_input in self.crops:
                session.update("ENTER_QTY", crop=self.crops[user_input])
                return ChannelResponse(f"Enter {self.crops[user_input]} qty (bags):", True)
            return ChannelResponse("Invalid crop.", False)

        if state == "ENTER_QTY":
            try:
                qty = float(user_input)
                session.update("SELECT_GRADE", qty=qty)
                return ChannelResponse("Select Grade:\n1. A\n2. B\n3. C", True)
            except:
                return ChannelResponse("Enter a number.", True)

        if state == "SELECT_GRADE":
            if user_input in self.grades:
                grade = self.grades[user_input]
                crop = session.data.get("crop")
                qty = session.data.get("qty")
                return ChannelResponse(f"✓ Recorded: {qty} bags Grade {grade} {crop}", False)
            return ChannelResponse("Invalid grade.", False)

        return ChannelResponse("Session Error.", False)
