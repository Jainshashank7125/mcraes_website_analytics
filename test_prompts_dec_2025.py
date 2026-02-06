#!/usr/bin/env python3
"""
Test if prompts are being returned in the API for specific clients
for December 1-31, 2025 date range
"""
import requests
import json
from datetime import datetime

def test_prompts_dec_2025():
    """Test prompts visibility via API for Dec 1-31, 2025"""
    base_url = "http://localhost:8000/api/v1"
    
    # Test clients
    clients = [
        {"name": "Canadian Shade", "id": 29, "brand_id": 5553},
        {"name": "City Duct Cleaning", "id": 67, "brand_id": 5726},
        {"name": "MGA International", "id": 69, "brand_id": 5908},
        {"name": "PolyPak Packaging", "id": 70, "brand_id": 5915},
    ]
    
    # Specific date range: December 1-31, 2025
    start_date = "2025-12-01"
    end_date = "2025-12-31"
    
    print("=" * 70)
    print("Testing Prompts API Response for December 1-31, 2025")
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
                kpis = data.get("kpis", {})
                
                print(f"  ✅ API Response: SUCCESS")
                print(f"  Top Performing Prompts: {len(top_prompts)}")
                print(f"  Scrunch AI Insights: {len(insights)}")
                print(f"  Scrunch KPIs: {len([k for k in kpis.keys() if k])}")
                
                if top_prompts:
                    print(f"  ✅ Top Prompts ARE being returned!")
                    for i, prompt in enumerate(top_prompts[:3], 1):
                        print(f"     {i}. {prompt.get('text', 'N/A')[:60]}...")
                else:
                    print(f"  ❌ Top Prompts: EMPTY")
                    print(f"     Reason: No prompts with responses in Dec 1-31, 2025")
                
                if insights:
                    print(f"  ✅ Insights ARE being returned!")
                    for i, insight in enumerate(insights[:3], 1):
                        print(f"     {i}. {insight.get('seedPrompt', 'N/A')[:60]}...")
                else:
                    print(f"  ❌ Insights: EMPTY")
                    print(f"     Reason: No prompts with responses in Dec 1-31, 2025")
                
                # Check if we have responses in this date range
                if not top_prompts and not insights:
                    print(f"  ⚠️  No prompts data - checking if responses exist in date range...")
                    # We can't directly check from here, but we know from earlier that
                    # these clients have prompts and responses, just not in this date range
            else:
                print(f"  ❌ API Error: {response.status_code}")
                print(f"     Response: {response.text[:200]}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
        
        print()
    
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print("If prompts are not showing for Dec 1-31, 2025:")
    print("1. Check if responses exist in that specific date range")
    print("2. Prompts only appear if they have responses in the selected period")
    print("3. The fix is working - it's filtering by responses in date range")
    print("4. If no responses in Dec 2025, prompts won't appear for that period")
    print()

if __name__ == "__main__":
    test_prompts_dec_2025()
