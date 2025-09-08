#!/usr/bin/env python3
"""
Backend API Tests for Health Reminder App
Tests all endpoints for elderly health reminder system
"""

import requests
import json
from datetime import datetime, date
import time
import sys

# Backend URL from frontend .env
BACKEND_URL = "https://senior-movement.preview.emergentagent.com/api"

class HealthReminderAPITester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.session_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if response_data and not success:
            print(f"   Response: {response_data}")
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'response': response_data
        })
        
    def test_health_check(self):
        """Test basic API health check"""
        try:
            response = requests.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                if "Health Reminder API" in data.get("message", ""):
                    self.log_test("Health Check", True, "API is responding correctly")
                    return True
                else:
                    self.log_test("Health Check", False, "Unexpected response format", data)
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Health Check", False, f"Connection error: {str(e)}")
        return False
        
    def test_create_session(self):
        """Test creating a new health session"""
        try:
            # Test data for elderly user - 50 min sitting, 10 min activity
            session_data = {
                "sitting_duration": 50,
                "activity_duration": 10,
                "completed": False
            }
            
            response = requests.post(
                f"{self.base_url}/sessions",
                json=session_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if "id" in data and data["sitting_duration"] == 50:
                    self.session_id = data["id"]  # Store for later tests
                    self.log_test("Create Session", True, f"Session created with ID: {self.session_id}")
                    return True
                else:
                    self.log_test("Create Session", False, "Invalid response structure", data)
            else:
                self.log_test("Create Session", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Create Session", False, f"Request error: {str(e)}")
        return False
        
    def test_get_today_sessions(self):
        """Test getting today's sessions"""
        try:
            response = requests.get(f"{self.base_url}/sessions/today")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    session_count = len(data)
                    self.log_test("Get Today Sessions", True, f"Retrieved {session_count} sessions for today")
                    return True
                else:
                    self.log_test("Get Today Sessions", False, "Response is not a list", data)
            else:
                self.log_test("Get Today Sessions", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get Today Sessions", False, f"Request error: {str(e)}")
        return False
        
    def test_daily_progress(self):
        """Test getting daily progress summary"""
        try:
            response = requests.get(f"{self.base_url}/sessions/progress")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["date", "total_sessions", "completed_sessions", "total_sitting_time", "total_activity_time", "sessions"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Daily Progress", True, f"Progress: {data['total_sessions']} sessions, {data['completed_sessions']} completed")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Daily Progress", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Daily Progress", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Daily Progress", False, f"Request error: {str(e)}")
        return False
        
    def test_weekly_progress(self):
        """Test getting weekly progress"""
        try:
            response = requests.get(f"{self.base_url}/sessions/weekly")
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["week_start", "week_end", "daily_progress"]
                
                if all(field in data for field in required_fields):
                    daily_count = len(data["daily_progress"])
                    self.log_test("Weekly Progress", True, f"Weekly data with {daily_count} days of progress")
                    return True
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Weekly Progress", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Weekly Progress", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Weekly Progress", False, f"Request error: {str(e)}")
        return False
        
    def test_complete_session(self):
        """Test marking a session as completed"""
        if not self.session_id:
            self.log_test("Complete Session", False, "No session ID available (create session test must pass first)")
            return False
            
        try:
            response = requests.post(f"{self.base_url}/sessions/{self.session_id}/complete")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("completed") == True:
                    self.log_test("Complete Session", True, f"Session {self.session_id} marked as completed")
                    return True
                else:
                    self.log_test("Complete Session", False, "Session not marked as completed", data)
            else:
                self.log_test("Complete Session", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Complete Session", False, f"Request error: {str(e)}")
        return False
        
    def test_complete_invalid_session(self):
        """Test completing a non-existent session"""
        try:
            fake_id = "invalid-session-id-12345"
            response = requests.post(f"{self.base_url}/sessions/{fake_id}/complete")
            
            if response.status_code == 404:
                self.log_test("Complete Invalid Session", True, "Correctly returned 404 for invalid session ID")
                return True
            else:
                self.log_test("Complete Invalid Session", False, f"Expected 404, got {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Complete Invalid Session", False, f"Request error: {str(e)}")
        return False
        
    def test_get_user_settings(self):
        """Test getting user settings"""
        try:
            response = requests.get(f"{self.base_url}/settings")
            
            if response.status_code == 200:
                data = response.json()
                expected_fields = ["sitting_reminder_minutes", "activity_break_minutes", "notifications_enabled", "sound_alerts_enabled", "daily_goal_sessions"]
                
                if all(field in data for field in expected_fields):
                    self.log_test("Get User Settings", True, f"Settings: {data['sitting_reminder_minutes']}min sitting, {data['activity_break_minutes']}min activity")
                    return True
                else:
                    missing = [f for f in expected_fields if f not in data]
                    self.log_test("Get User Settings", False, f"Missing fields: {missing}", data)
            else:
                self.log_test("Get User Settings", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Get User Settings", False, f"Request error: {str(e)}")
        return False
        
    def test_update_user_settings(self):
        """Test updating user settings"""
        try:
            # Update settings for elderly user - longer sitting time, shorter activity
            update_data = {
                "sitting_reminder_minutes": 60,  # Increase to 60 minutes
                "activity_break_minutes": 15,    # Increase to 15 minutes
                "notifications_enabled": True,
                "sound_alerts_enabled": True,
                "daily_goal_sessions": 6         # Reduce to 6 sessions per day
            }
            
            response = requests.put(
                f"{self.base_url}/settings",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("sitting_reminder_minutes") == 60 and 
                    data.get("activity_break_minutes") == 15 and
                    data.get("daily_goal_sessions") == 6):
                    self.log_test("Update User Settings", True, "Settings updated successfully")
                    return True
                else:
                    self.log_test("Update User Settings", False, "Settings not updated correctly", data)
            else:
                self.log_test("Update User Settings", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Update User Settings", False, f"Request error: {str(e)}")
        return False
        
    def test_partial_settings_update(self):
        """Test partial update of user settings"""
        try:
            # Only update notification settings
            update_data = {
                "notifications_enabled": False,
                "sound_alerts_enabled": False
            }
            
            response = requests.put(
                f"{self.base_url}/settings",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if (data.get("notifications_enabled") == False and 
                    data.get("sound_alerts_enabled") == False):
                    self.log_test("Partial Settings Update", True, "Partial settings update successful")
                    return True
                else:
                    self.log_test("Partial Settings Update", False, "Partial update failed", data)
            else:
                self.log_test("Partial Settings Update", False, f"HTTP {response.status_code}", response.text)
        except Exception as e:
            self.log_test("Partial Settings Update", False, f"Request error: {str(e)}")
        return False
        
    def run_all_tests(self):
        """Run all API tests"""
        print(f"🏥 Starting Health Reminder API Tests")
        print(f"🔗 Backend URL: {self.base_url}")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            self.test_health_check,
            self.test_create_session,
            self.test_get_today_sessions,
            self.test_daily_progress,
            self.test_weekly_progress,
            self.test_complete_session,
            self.test_complete_invalid_session,
            self.test_get_user_settings,
            self.test_update_user_settings,
            self.test_partial_settings_update
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            test()
            time.sleep(0.5)  # Small delay between tests
            
        # Count results
        passed = sum(1 for result in self.test_results if result['success'])
        
        print("=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Health Reminder API is working correctly.")
            return True
        else:
            failed_tests = [r['test'] for r in self.test_results if not r['success']]
            print(f"❌ Failed tests: {', '.join(failed_tests)}")
            return False

def main():
    """Main test execution"""
    tester = HealthReminderAPITester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()