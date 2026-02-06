#!/usr/bin/env python3
"""
Test if prompts are being returned in the API for specific clients
"""
import requests
import json
from datetime import datetime, timedelta

def test_prompts_api():
    """Test prompts visibility via API"""
    base_url = "http://localhost:8000/api/v1"
    
    # Test clients
    clients = [
        {"name": "Canadian Shade", "id": 29, "brand_id": 5553},
        {"name": "City Duct Cleaning", "id": 67, "brand_id": 5726},
        {"name": "MGA International", "id": 69, "brand_id": 5908},
        {"name": "PolyPak Packaging", "id": 70, "brand_id": 5915},
    ]
    
    # Default date range (last 30 days)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print("=" * 70)
    print("Testing Prompts API Response")
    print("=" * 70)
    print(f"Date Range: {start_date} to {end_date}")
    print()
    
    for client in clients:
        print(f"Testing: {client['name']} (Client ID: {client['id']}, Brand ID: {client['brand_id']})")
        print("-" * 70)
        
        # Test 1: Scrunch dashboard endpoint
        try:
            url = f"{base_url}/data/reporting-dashboard/{client['brand_id']}/scrunch"
            params = {
                "client_id": client['id'],
                "start_date": start_date,
                "end_date": end_date
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                chart_data = data.get("chart_data", {})
                top_prompts = chart_data.get("top_performing_prompts", [])
                insights = chart_data.get("scrunch_ai_insights", [])
                
                print(f"  ✅ API Response: SUCCESS")
                print(f"  Top Performing Prompts: {len(top_prompts)}")
                print(f"  Scrunch AI Insights: {len(insights)}")
                
                if top_prompts:
                    print(f"  ✅ Top Prompts ARE being returned!")
                    print(f"     Sample: {top_prompts[0].get('text', 'N/A')[:50]}...")
                else:
                    print(f"  ⚠️  Top Prompts: EMPTY (may need responses in date range)")
                
                if insights:
                    print(f"  ✅ Insights ARE being returned!")
                    print(f"     Sample: {insights[0].get('seedPrompt', 'N/A')[:50]}...")
                else:
                    print(f"  ⚠️  Insights: EMPTY (may need responses in date range)")
            else:
                print(f"  ❌ API Error: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("If prompts are not showing:")
    print("1. Check if responses exist in the selected date range")
    print("2. Prompts are only shown if they have responses in that range")
    print("3. Try expanding the date range if needed")
    print()

if __name__ == "__main__":
    test_prompts_api()
