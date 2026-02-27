"""
Integration tests for FastAPI activities API endpoints.
Tests all endpoints and error scenarios.
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for the GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Science Club" in data

    def test_get_activities_response_structure(self, client):
        """Test that each activity has the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        
        assert isinstance(activity["participants"], list)
        assert isinstance(activity["max_participants"], int)

    def test_get_activities_includes_initial_participants(self, client):
        """Test that activities include their initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Chess Club should have 2 initial participants
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""

    def test_signup_successfully(self, client):
        """Test successful signup for an activity."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity."""
        email = "newstudent@mergington.edu"
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity(self, client):
        """Test that signup fails for a non-existent activity."""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_fails(self, client):
        """Test that signing up for the same activity twice fails."""
        email = "michael@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client):
        """Test that multiple students can sign up for the same activity."""
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": student1}
        )
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": student2}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both are added
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert student1 in participants
        assert student2 in participants

    def test_signup_same_student_different_activities(self, client):
        """Test that the same student can sign up for multiple activities."""
        email = "versatile@mergington.edu"
        
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        response2 = client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify in both activities
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Art Studio"]["participants"]

    def test_signup_url_encoded_activity_name(self, client):
        """Test signup with an activity name that has spaces."""
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "coder@mergington.edu"}
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_successfully(self, client):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant."""
        email = "michael@mergington.edu"
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity(self, client):
        """Test that unregister fails for a non-existent activity."""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_registered_student(self, client):
        """Test that unregistering a student who isn't registered fails."""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "unregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_and_reregister(self, client):
        """Test that a student can unregister and then register again."""
        email = "michael@mergington.edu"
        
        # Unregister
        response1 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up again
        response2 = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify registered
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Chess Club"]["participants"]


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_signup_empty_email(self, client):
        """Test signup with empty email parameter."""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": ""}
        )
        # Should still process - email is technically provided
        assert response.status_code == 200

    def test_signup_special_characters_in_email(self, client):
        """Test signup with special characters in email."""
        email = "student+test@mergington.edu"
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200

    def test_activity_name_case_sensitive(self, client):
        """Test that activity names are case-sensitive."""
        response = client.post(
            "/activities/chess club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_concurrent_signups_to_same_activity(self, client):
        """Test multiple rapid signups to the same activity."""
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        email3 = "student3@mergington.edu"
        
        responses = [
            client.post("/activities/Gym Class/signup", params={"email": email1}),
            client.post("/activities/Gym Class/signup", params={"email": email2}),
            client.post("/activities/Gym Class/signup", params={"email": email3}),
        ]
        
        assert all(r.status_code == 200 for r in responses)
        
        # Verify all are registered
        response = client.get("/activities")
        participants = response.json()["Gym Class"]["participants"]
        assert email1 in participants
        assert email2 in participants
        assert email3 in participants


class TestActivityIntegrity:
    """Tests to verify data integrity across operations."""

    def test_operations_do_not_affect_other_activities(self, client):
        """Test that operations on one activity don't affect others."""
        email = "student@mergington.edu"
        original_participants = {}
        
        # Get initial state of all activities except Chess Club
        response = client.get("/activities")
        for activity_name in response.json():
            if activity_name != "Chess Club":
                original_participants[activity_name] = len(
                    response.json()[activity_name]["participants"]
                )
        
        # Signup for Chess Club
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        
        # Verify other activities unchanged
        response = client.get("/activities")
        for activity_name in original_participants:
            assert len(response.json()[activity_name]["participants"]) == original_participants[activity_name]

    def test_participant_count_accuracy(self, client):
        """Test that participant count remains accurate after operations."""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        # Signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": "student1@mergington.edu"}
        )
        
        response = client.get("/activities")
        assert len(response.json()["Chess Club"]["participants"]) == initial_count + 1
        
        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "student1@mergington.edu"}
        )
        
        response = client.get("/activities")
        assert len(response.json()["Chess Club"]["participants"]) == initial_count
