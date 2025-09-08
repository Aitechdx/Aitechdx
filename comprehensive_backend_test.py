#!/usr/bin/env python3
"""
Comprehensive Backend API Tests for Health Reminder App
Tests data persistence and multiple session scenarios
"""

import requests
import json
from datetime import datetime, date
import time
import sys

# Backend URL from frontend .env
BACKEND_URL = "https://senior-movement.preview.emergentagent.com/api"

def test_multiple_sessions_and_progress():
    """Test creating multiple sessions and tracking progress"""
    print("🔄 Testing Multiple Sessions and Progress Tracking")
    print("=" * 50)
    
    # Create multiple sessions for elderly user scenarios
    sessions_data = [
        {"sitting_duration": 50, "activity_duration": 10, "completed": False},
        {"sitting_duration": 45, "activity_duration": 15, "completed": False},
        {"sitting_duration": 60, "activity_duration": 10, "completed": False},
        {"sitting_duration": 55, "activity_duration": 12, "completed": False}
    ]
    
    session_ids = []
    
    # Create sessions
    for i, session_data in enumerate(sessions_data):
        response = requests.post(
            f"{BACKEND_URL}/sessions",
            json=session_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            session_ids.append(data["id"])
            print(f"✅ Session {i+1} created: {session_data['sitting_duration']}min sitting, {session_data['activity_duration']}min activity")
        else:
            print(f"❌ Failed to create session {i+1}: {response.status_code}")
            return False
    
    # Complete some sessions
    for i in range(2):  # Complete first 2 sessions
        response = requests.post(f"{BACKEND_URL}/sessions/{session_ids[i]}/complete")
        if response.status_code == 200:
            print(f"✅ Session {i+1} marked as completed")
        else:
            print(f"❌ Failed to complete session {i+1}")
    
    # Check daily progress
    response = requests.get(f"{BACKEND_URL}/sessions/progress")
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Daily Progress:")
        print(f"   Total Sessions: {data['total_sessions']}")
        print(f"   Completed Sessions: {data['completed_sessions']}")
        print(f"   Total Sitting Time: {data['total_sitting_time']} minutes")
        print(f"   Total Activity Time: {data['total_activity_time']} minutes")
        
        # Verify the numbers make sense
        if data['total_sessions'] >= 4 and data['completed_sessions'] >= 2:
            print("✅ Progress tracking working correctly")
            return True
        else:
            print("❌ Progress numbers don't match expected values")
            return False
    else:
        print(f"❌ Failed to get daily progress: {response.status_code}")
        return False

def test_settings_persistence():
    """Test that settings persist across requests"""
    print("\n🔧 Testing Settings Persistence")
    print("=" * 30)
    
    # Set specific settings for elderly users
    elderly_settings = {
        "sitting_reminder_minutes": 45,  # Shorter for elderly comfort
        "activity_break_minutes": 20,   # Longer break time
        "notifications_enabled": True,
        "sound_alerts_enabled": True,
        "daily_goal_sessions": 5        # Realistic goal for elderly
    }
    
    # Update settings
    response = requests.put(
        f"{BACKEND_URL}/settings",
        json=elderly_settings,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        print("✅ Settings updated successfully")
    else:
        print(f"❌ Failed to update settings: {response.status_code}")
        return False
    
    # Retrieve settings to verify persistence
    response = requests.get(f"{BACKEND_URL}/settings")
    if response.status_code == 200:
        data = response.json()
        
        # Check if all settings match
        matches = (
            data.get("sitting_reminder_minutes") == 45 and
            data.get("activity_break_minutes") == 20 and
            data.get("daily_goal_sessions") == 5 and
            data.get("notifications_enabled") == True and
            data.get("sound_alerts_enabled") == True
        )
        
        if matches:
            print("✅ Settings persistence verified")
            print(f"   Sitting reminder: {data['sitting_reminder_minutes']} minutes")
            print(f"   Activity break: {data['activity_break_minutes']} minutes")
            print(f"   Daily goal: {data['daily_goal_sessions']} sessions")
            return True
        else:
            print("❌ Settings don't match expected values")
            print(f"   Retrieved: {data}")
            return False
    else:
        print(f"❌ Failed to retrieve settings: {response.status_code}")
        return False

def test_weekly_progress():
    """Test weekly progress endpoint with existing data"""
    print("\n📅 Testing Weekly Progress")
    print("=" * 25)
    
    response = requests.get(f"{BACKEND_URL}/sessions/weekly")
    if response.status_code == 200:
        data = response.json()
        
        print(f"📊 Weekly Progress Summary:")
        print(f"   Week Start: {data['week_start']}")
        print(f"   Week End: {data['week_end']}")
        print(f"   Days with Data: {len(data['daily_progress'])}")
        
        # Check if today's data is included
        today_str = date.today().isoformat()
        today_data = None
        for day in data['daily_progress']:
            if day['date'] == today_str:
                today_data = day
                break
        
        if today_data:
            print(f"   Today's Sessions: {today_data['total_sessions']}")
            print(f"   Today's Completed: {today_data['completed_sessions']}")
            print("✅ Weekly progress includes today's data")
            return True
        else:
            print("❌ Today's data not found in weekly progress")
            return False
    else:
        print(f"❌ Failed to get weekly progress: {response.status_code}")
        return False

def main():
    """Run comprehensive tests"""
    print("🏥 Comprehensive Health Reminder API Tests")
    print("🔗 Backend URL:", BACKEND_URL)
    print("=" * 60)
    
    tests = [
        test_multiple_sessions_and_progress,
        test_settings_persistence,
        test_weekly_progress
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(1)  # Small delay between tests
    
    print("\n" + "=" * 60)
    print(f"📊 Comprehensive Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All comprehensive tests passed! API is production-ready.")
        return True
    else:
        print("❌ Some comprehensive tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)