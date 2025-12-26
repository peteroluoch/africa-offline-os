import uuid

import requests

BASE_URL = "http://localhost:8000"

def test_flow(inputs):
    session_id = f"test_{uuid.uuid4().hex[:8]}"
    print(f"\n--- Testing Flow: {inputs} (Session: {session_id}) ---")

    history = []
    last_resp = ""

    # Initial request
    resp = requests.post(f"{BASE_URL}/channels/ussd", json={
        "sessionId": session_id,
        "phoneNumber": "+254700000000",
        "text": ""
    })
    last_resp = resp.text
    print(f"Start: {last_resp}")

    for i in inputs:
        history.append(i)
        text = "*".join(history)
        resp = requests.post(f"{BASE_URL}/channels/ussd", json={
            "sessionId": session_id,
            "phoneNumber": "+254700000000",
            "text": text
        })
        last_resp = resp.text
        print(f"Input '{i}': {last_resp}")

    return last_resp

if __name__ == "__main__":
    # Test Agri Flow
    res = test_flow(["1", "1", "1", "15", "1"])
    assert "Recorded" in res

    # Test Transport Check Route
    res = test_flow(["2", "1", "1"])
    assert "Route 46" in res

    # Test Transport Driver Report
    res = test_flow(["2", "2", "KCA123X", "1"])
    assert "Status updated" in res

    print("\n✅ All Flows Verified!")
