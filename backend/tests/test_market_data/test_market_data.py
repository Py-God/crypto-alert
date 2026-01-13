# test_market_data.py
import requests
import time

BASE_URL = "http://localhost:8000/api/v1/market"

def test_market_data():
    print("🧪 Testing Market Data Module\n")
    
    # Test 1: Get crypto price
    print("  Getting BTC price...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/price/BTC", params={"asset_type": "crypto"})
    elapsed = time.time() - start
    assert response.status_code == 200
    btc_price = response.json()
    print(f"   ✅ BTC Price: ${btc_price['price']:,.2f} (took {elapsed:.2f}s)")
    
    # Test 2: Get stock price
    print("\n  Getting AAPL price...")
    response = requests.get(f"{BASE_URL}/price/AAPL", params={"asset_type": "stock"})
    assert response.status_code == 200
    aapl_price = response.json()
    print(f"   ✅ AAPL Price: ${aapl_price['price']:,.2f}")
    
    # Test 3: Test caching
    print("\n  Testing cache (getting BTC again)...")
    start = time.time()
    response = requests.get(f"{BASE_URL}/price/BTC", params={"asset_type": "crypto"})
    elapsed = time.time() - start
    assert response.status_code == 200
    print(f"   ✅ Cached response took {elapsed:.2f}s (should be faster!)")
    
    # Test 4: Multiple prices
    print("\n  Getting multiple crypto prices...")
    response = requests.post(f"{BASE_URL}/prices", json={
        "symbols": ["BTC", "ETH", "BNB"],
        "asset_type": "crypto"
    })
    assert response.status_code == 200
    prices = response.json()
    print(f"   ✅ Got {len(prices['prices'])} prices:")
    for symbol, data in prices['prices'].items():
        print(f"      {symbol}: ${data['price']:,.2f}")
    
    # Test 5: Validate valid symbol
    print("\n  Validating BTC symbol...")
    response = requests.get(f"{BASE_URL}/validate/BTC", params={"asset_type": "crypto"})
    assert response.status_code == 200
    result = response.json()
    assert result['valid'] == True
    print(f"   ✅ BTC is valid: {result['valid']}")
    
    # Test 6: Validate invalid symbol
    print("\n  Validating invalid symbol...")
    response = requests.get(f"{BASE_URL}/validate/FAKECOIN", params={"asset_type": "crypto"})
    assert response.status_code == 200
    result = response.json()
    assert result['valid'] == False
    print(f"   ✅ FAKECOIN is invalid: {result['valid']}")
    
    # Test 7: Try to get invalid symbol (should fail)
    print("\n  Trying to get price for invalid symbol...")
    response = requests.get(f"{BASE_URL}/price/INVALID", params={"asset_type": "crypto"})
    assert response.status_code == 404
    print(f"   ✅ Correctly returned 404: {response.json()['detail']}")
    
    print("\n✅ All market data tests passed!")

if __name__ == "__main__":
    test_market_data()