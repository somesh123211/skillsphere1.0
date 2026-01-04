from locust import HttpUser, task, between

# ==============================
# CONFIG
# ==============================
ADMIN_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZG1pbl91aWQiOiJiZDExMGNjMi04NjJiLTQyODEtYjcxZS0zOGI4YWYxNjAxNWQiLCJ0eXBlIjoiYWRtaW4iLCJleHAiOjE3Njc1NjgzOTV9.8E3HDI12I9AvmgzGpwR4t8VRtRR-xrl_myWIzKmRrSg"

class AdminUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Use fixed JWT (no OTP, no login load)
        self.headers = {
            "Authorization": f"Bearer {ADMIN_JWT}"
        }

    # ==============================
    # ADMIN DASHBOARD APIs
    # ==============================

    @task(4)
    def students_year_2(self):
        self.client.get(
            "/api/admin/students?year=2",
            headers=self.headers
        )

    @task(4)
    def students_year_3(self):
        self.client.get(
            "/api/admin/students?year=3",
            headers=self.headers
        )

    @task(2)
    def faculty_quiz_master(self):
        self.client.get(
            "/api/admin/faculty-quiz/master",
            headers=self.headers
        )

    @task(1)
    def daily_leaderboard(self):
        self.client.get(
            "/api/admin/leaderboard/daily?year=2&type=all",
            headers=self.headers
        )
