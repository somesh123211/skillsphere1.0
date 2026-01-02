
from locust import HttpUser, task, between
import random

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1aWQiOjI1MTAxMDAxLCJleHAiOjE3Njc0MTM1MTR9.-IC9p235AeRH5Gv-d2iFXgbIgS7qdCYF_dcrNEuHO54"


HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

class SkillSphereStressUser(HttpUser):
    # 🔥 very aggressive user behavior
    wait_time = between(0.1, 0.5)

    @task(5)
    def dashboard_heavy(self):
        self.client.get("/api/leaderboard", headers=HEADERS)
        self.client.get("/api/quiz/today/status", headers=HEADERS)

    @task(4)
    def profile_heavy(self):
        self.client.get("/get_student_profile", headers=HEADERS)
        self.client.get("/api/profile/status?year=2", headers=HEADERS)

    @task(3)
    def review_heavy(self):
        self.client.get(
            "/api/profile/review?year=2&quiz_date=2026-01-02",
            headers=HEADERS
        )

    @task(2)
    def faculty_quiz_checks(self):
        self.client.get("/api/profile/faculty_quiz/today", headers=HEADERS)
        self.client.get("/api/profile/faculty_quiz/history", headers=HEADERS)

    @task(1)
    def random_noise(self):
        # simulate unpredictable user behavior
        choice = random.choice([
            "/api/leaderboard",
            "/api/quiz/today/status",
            "/get_student_profile"
        ])
        self.client.get(choice, headers=HEADERS)
