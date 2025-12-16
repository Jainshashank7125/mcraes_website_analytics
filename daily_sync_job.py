"""
Daily Sync Job - Runs at 11:30 PM IST (scheduled via cron)
Syncs AgencyAnalytics, GA4, and Scrunch AI data automatically
All syncs use "complete" mode to sync all active clients/campaigns
"""
import sys
import os
import requests
import time
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

API_BASE = "http://localhost:8000/api/v1"

def sync_scrunch_data():
    """Sync Scrunch AI data (brands, prompts, responses) - Complete mode"""
    print("=" * 70)
    print("Syncing Scrunch AI Data (Complete Mode)")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Sync all Scrunch AI data in complete mode (sync_mode=complete)
        # Timeout: ~30 minutes (1800 seconds)
        # Pass cron=true to bypass authentication
        response = requests.post(
            f"{API_BASE}/sync/all",
            params={"sync_mode": "complete", "cron": True},
            timeout=1800  # 30 min timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            if "job_id" in data:
                # Async job started
                job_id = data.get("job_id")
                print(f"[INFO] Scrunch AI sync job started (job_id: {job_id})")
                print("  Note: This is an async job. Check job status via API to see completion.")
                return True
            else:
                # Synchronous response (legacy)
                summary = data.get("summary", {})
                print("[SUCCESS] Scrunch AI sync completed")
                print(f"  Brands: {summary.get('brands', 0)}")
                print(f"  Prompts: {summary.get('total_prompts', 0)}")
                print(f"  Responses: {summary.get('total_responses', 0)}")
                return True
        else:
            print(f"[ERROR] Scrunch AI sync failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[ERROR] Scrunch AI sync timed out (>30 minutes)")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API server")
        print("  Make sure the server is running: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"[ERROR] Scrunch AI sync error: {e}")
        return False

def sync_ga4_data():
    """Sync GA4 data for all clients with GA4 configured - Complete mode"""
    print()
    print("=" * 70)
    print("Syncing GA4 Data (Complete Mode)")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Sync GA4 data (last 30 days, skip realtime to avoid errors)
        # Complete mode: syncs all clients with GA4 property ID mapped
        # Pass cron=true to bypass authentication
        response = requests.post(
            f"{API_BASE}/sync/ga4",
            params={
                "sync_mode": "complete",
                "sync_realtime": False,  # Skip realtime to avoid API errors
                "cron": True
            },
            timeout=3600  # 60 min timeout (GA4 can take longer)
        )
        
        if response.status_code == 200:
            data = response.json()
            if "job_id" in data:
                # Async job started
                job_id = data.get("job_id")
                print(f"[INFO] GA4 sync job started (job_id: {job_id})")
                print("  Note: This is an async job. Check job status via API to see completion.")
                return True
            else:
                # Synchronous response (legacy)
                total_synced = data.get("total_synced", {})
                print("[SUCCESS] GA4 sync completed")
                print(f"  Clients synced: {total_synced.get('clients', 0)}")
                print(f"  Traffic overview: {total_synced.get('traffic_overview', 0)}")
                print(f"  Top pages: {total_synced.get('top_pages', 0)}")
                print(f"  Traffic sources: {total_synced.get('traffic_sources', 0)}")
                print(f"  Geographic: {total_synced.get('geographic', 0)}")
                print(f"  Devices: {total_synced.get('devices', 0)}")
                print(f"  Conversions: {total_synced.get('conversions', 0)}")
                return True
        else:
            print(f"[ERROR] GA4 sync failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[ERROR] GA4 sync timed out (>60 minutes)")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API server")
        return False
    except Exception as e:
        print(f"[ERROR] GA4 sync error: {e}")
        return False

def sync_agency_analytics_data():
    """Sync AgencyAnalytics data for all active clients - Complete mode"""
    print()
    print("=" * 70)
    print("Syncing Agency Analytics Data (Complete Mode)")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Sync AgencyAnalytics data in complete mode
        # Complete mode: syncs all active clients
        # Timeout: >2 hours (7200 seconds) as AgencyAnalytics sync can take a long time
        # Pass cron=true to bypass authentication
        response = requests.post(
            f"{API_BASE}/sync/agency-analytics",
            params={"sync_mode": "complete", "cron": True},
            timeout=7200  # 2 hours timeout (AgencyAnalytics may take >2 hours)
        )
        
        if response.status_code == 200:
            data = response.json()
            if "job_id" in data:
                # Async job started
                job_id = data.get("job_id")
                print(f"[INFO] Agency Analytics sync job started (job_id: {job_id})")
                print("  Note: This is an async job that may take >2 hours. Check job status via API to see completion.")
                return True
            else:
                # Synchronous response (legacy)
                total_synced = data.get("total_synced", {})
                print("[SUCCESS] Agency Analytics sync completed")
                print(f"  Campaigns: {total_synced.get('campaigns', 0)}")
                print(f"  Clients: {total_synced.get('clients', 0)}")
                print(f"  Rankings: {total_synced.get('rankings', 0)}")
                print(f"  Keywords: {total_synced.get('keywords', 0)}")
                print(f"  Keyword Rankings: {total_synced.get('keyword_rankings', 0)}")
                return True
        else:
            print(f"[ERROR] Agency Analytics sync failed: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("[ERROR] Agency Analytics sync timed out (>2 hours)")
        print("  Note: This sync can take a very long time. Consider checking job status manually.")
        return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] Cannot connect to API server")
        return False
    except Exception as e:
        print(f"[ERROR] Agency Analytics sync error: {e}")
        return False

def generate_ga4_token():
    """Generate GA4 access token (needed daily)"""
    print()
    print("=" * 70)
    print("Generating GA4 Access Token")
    print("=" * 70)
    print()
    
    try:
        # Import and run token generator
        import subprocess
        import sys
        
        result = subprocess.run(
            [sys.executable, "generate_ga4_token.py"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            print("[SUCCESS] GA4 token generated/verified")
            if result.stdout:
                # Print only key lines from output
                for line in result.stdout.split('\n'):
                    if 'SUCCESS' in line or 'Token' in line or 'token' in line.lower():
                        print(f"  {line}")
            return True
        else:
            print("[WARNING] Failed to generate GA4 token")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Token generation error: {e}")
        return False

def main():
    """Main sync job - runs all syncs at 11:30 PM IST"""
    print()
    print("=" * 70)
    print("Daily Sync Job - Started")
    print("=" * 70)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("Note: All syncs run in 'complete' mode to sync all active clients/campaigns")
    print()
    
    results = {
        "ga4_token": False,
        "agency_analytics": False,
        "ga4_data": False,
        "scrunch": False
    }
    
    # Step 1: Generate GA4 token first (needed for GA4 API calls)
    results["ga4_token"] = generate_ga4_token()
    
    # Step 2: Sync AgencyAnalytics data (all active clients)
    # Run this first as it may take >2 hours
    results["agency_analytics"] = sync_agency_analytics_data()
    
    # Step 3: Sync GA4 data (all clients with GA4 property ID mapped)
    results["ga4_data"] = sync_ga4_data()
    
    # Step 4: Sync Scrunch AI data (all clients linked to Scrunch)
    # Run this last as it's faster (~30 mins)
    results["scrunch"] = sync_scrunch_data()
    
    # Summary
    print()
    print("=" * 70)
    print("Daily Sync Job - Summary")
    print("=" * 70)
    print(f"GA4 Token: {'SUCCESS' if results['ga4_token'] else 'FAILED'}")
    print(f"Agency Analytics Sync: {'SUCCESS' if results['agency_analytics'] else 'FAILED'}")
    print(f"GA4 Data Sync: {'SUCCESS' if results['ga4_data'] else 'FAILED'}")
    print(f"Scrunch AI Sync: {'SUCCESS' if results['scrunch'] else 'FAILED'}")
    print()
    print("Note: Async jobs may still be running. Check job status via API to verify completion.")
    print()
    
    # Count successes (excluding token generation for overall status)
    sync_successes = sum([
        results["agency_analytics"],
        results["ga4_data"],
        results["scrunch"]
    ])
    
    if sync_successes >= 2:  # At least 2 out of 3 syncs should succeed
        print("[SUCCESS] Most syncs completed successfully!")
        return 0
    else:
        print("[WARNING] Some syncs failed. Check logs above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

