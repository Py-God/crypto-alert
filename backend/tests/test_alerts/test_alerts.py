# test_alerts.py
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login first
def get_token():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "john@example.com",
        "password": "SecurePass123"
    })
    return response.json()["access_token"]

def test_alerts():
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🧪 Testing Alerts Module\n")
    
    # Test 1: Create crypto alert
    print("  Creating BTC alert...")
    response = requests.post(f"{BASE_URL}/alerts", headers=headers, json={
        "symbol": "BTC",
        "asset_type": "crypto",
        "alert_type": "above",
        "target_price": 50000,
        "notify_email": True,
        "notify_websocket": True
    })
    assert response.status_code == 201
    btc_alert = response.json()
    print(f"   ✅ Created alert ID: {btc_alert['id']}")
    
    # Test 2: Create stock alert
    print("\n  Creating AAPL alert...")
    response = requests.post(f"{BASE_URL}/alerts", headers=headers, json={
        "symbol": "AAPL",
        "asset_type": "stock",
        "alert_type": "below",
        "target_price": 150,
        "notify_email": True
    })
    assert response.status_code == 201
    aapl_alert = response.json()
    print(f"   ✅ Created alert ID: {aapl_alert['id']}")
    
    # Test 3: Get all alerts
    print("\n  Getting all alerts...")
    response = requests.get(f"{BASE_URL}/alerts", headers=headers)
    assert response.status_code == 200
    alerts_data = response.json()
    print(f"   ✅ Total alerts: {alerts_data['total']}")
    
    # Test 4: Get statistics
    print("\n  Getting alert statistics...")
    response = requests.get(f"{BASE_URL}/alerts/stats", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    print(f"   ✅ Active alerts: {stats['active_alerts']}")
    
    # Test 5: Update alert
    print("\n  Updating BTC alert...")
    response = requests.put(
        f"{BASE_URL}/alerts/{btc_alert['id']}",
        headers=headers,
        json={"target_price": 55000, "status": "paused"}
    )
    assert response.status_code == 200
    updated = response.json()
    assert updated['target_price'] == 55000
    assert updated['status'] == 'paused'
    print(f"   ✅ Updated to ${updated['target_price']} and paused")
    
    # Test 6: Delete alert
    print("\n  Deleting AAPL alert...")
    response = requests.delete(
        f"{BASE_URL}/alerts/{aapl_alert['id']}",
        headers=headers
    )
    assert response.status_code == 204
    print(f"   ✅ Alert deleted")
    
    # Test 7: Verify deletion
    print("\n  Verifying deletion...")
    response = requests.get(
        f"{BASE_URL}/alerts/{aapl_alert['id']}",
        headers=headers
    )
    assert response.status_code == 404
    print(f"   ✅ Alert not found (correctly deleted)")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    test_alerts()