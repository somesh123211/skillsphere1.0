# API Documentation - AI-Powered Placement Platform

## Base URL
```
http://localhost:5000
```

## Authentication
Most endpoints require a student email for identification. Include the email in the request body or as a parameter.

---

## 📚 Company-Specific Quizzes & Tests

### Get Company Quiz
```http
GET /api/quizzes/company/{company}
```

**Parameters:**
- `company` (path): Company name (tcs, infosys, microsoft, google, amazon, wipro)
- `type` (query): Quiz type (aptitude, coding)
- `difficulty` (query): Difficulty level (0.1-1.0, or "all")

**Response:**
```json
{
  "company": "tcs",
  "type": "aptitude",
  "questions": [
    {
      "id": 1,
      "question": "What is the output of: int x = 5; System.out.println(x++ + ++x);",
      "options": ["10", "11", "12", "13"],
      "correct": 2,
      "difficulty": 0.7,
      "topic": "Java Basics"
    }
  ],
  "total": 1
}
```

### Submit Assessment
```http
POST /api/assessments/submit
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "answers": [
    {
      "question_id": 1,
      "selected_option": 0,
      "topic": "Java Basics"
    }
  ],
  "time_taken": 120,
  "behavior_data": {
    "tab_switches": 2,
    "time_spent": [30, 45, 45],
    "answer_pattern": [0, 1, 2]
  }
}
```

**Response:**
```json
{
  "score": 85.5,
  "correct_answers": 8,
  "total_questions": 10,
  "insights": {
    "strengths": ["Excellent problem-solving skills"],
    "weaknesses": [],
    "recommendations": ["Focus on time management"],
    "predicted_score": 0.855
  },
  "suspicious": false
}
```

---

## 🧠 AI-Driven Adaptive Learning

### Get Next Adaptive Question
```http
POST /api/adaptive/next-question
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "topic": "general"
}
```

**Response:**
```json
{
  "question": {
    "id": 1,
    "question": "Question text...",
    "options": ["A", "B", "C", "D"],
    "correct": 1,
    "difficulty": 0.6,
    "topic": "Algorithms"
  },
  "predicted_difficulty": 0.65,
  "adaptive_reason": "Adjusted based on recent performance of 0.72"
}
```

---

## 📊 AI-Powered Insights & Recommendations

### Get Performance Insights
```http
GET /api/insights/performance/{student_email}
```

**Response:**
```json
{
  "insights": {
    "overall_performance": {
      "average_score": 78.5,
      "best_score": 95.0,
      "worst_score": 45.0,
      "total_assessments": 15,
      "improvement_trend": "improving"
    },
    "time_analysis": {
      "average_time": 180.5,
      "time_trend": "faster"
    },
    "recommendations": [
      "Focus on fundamental concepts and practice more basic problems"
    ],
    "weak_areas": ["Basic problem-solving skills"],
    "strong_areas": ["Problem-solving and analytical thinking"]
  },
  "performance_data": [...],
  "generated_at": "2024-01-15T10:30:00Z"
}
```

### Get Personalized Recommendations
```http
POST /api/insights/recommendations/{student_email}
```

**Request Body:**
```json
{
  "focus_area": "general"
}
```

**Response:**
```json
{
  "recommendations": {
    "study_plan": [
      "Week 1-2: Focus on basic concepts and fundamentals",
      "Week 3-4: Practice simple problems and build confidence"
    ],
    "resources": [
      "Basic programming tutorials",
      "Fundamental algorithm videos"
    ],
    "practice_areas": ["String manipulation", "Basic algorithms"],
    "timeline": {}
  },
  "confidence_score": 0.85,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

---

## 🎤 Interview Preparation Module

### Start Mock Interview
```http
POST /api/interview/mock-session
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "type": "technical",
  "company": "microsoft"
}
```

**Response:**
```json
{
  "session_id": "abc123def456",
  "questions": [
    {
      "id": 1,
      "question": "Explain the difference between a stack and a queue with examples.",
      "type": "data_structures",
      "difficulty": 0.6,
      "expected_keywords": ["lifo", "fifo", "push", "pop"]
    }
  ],
  "total_questions": 5,
  "estimated_duration": 15
}
```

### Submit Interview Answer
```http
POST /api/interview/submit-answer
```

**Request Body:**
```json
{
  "session_id": "abc123def456",
  "question_id": 1,
  "answer": "A stack is a LIFO data structure where elements are added and removed from the top..."
}
```

**Response:**
```json
{
  "feedback": {
    "score": 0.85,
    "strengths": ["Good use of relevant technical terms", "Comprehensive answer"],
    "improvements": ["Include more examples"],
    "keyword_coverage": 3,
    "sentiment": "positive"
  },
  "next_question": {
    "id": 2,
    "question": "How would you implement a hash table?",
    "type": "algorithms",
    "difficulty": 0.8
  }
}
```

---

## 🔍 Plagiarism & Cheating Detection

### Start Monitoring Session
```http
POST /api/monitoring/start-session
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "assessment_id": "assessment_123"
}
```

**Response:**
```json
{
  "session_id": "monitor_abc123",
  "monitoring_active": true,
  "message": "Monitoring session started"
}
```

### Log Monitoring Event
```http
POST /api/monitoring/log-event
```

**Request Body:**
```json
{
  "session_id": "monitor_abc123",
  "event_type": "tab_switch",
  "event_data": {
    "count": 3,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

**Response:**
```json
{
  "logged": true,
  "suspicious": false,
  "reason": null
}
```

---

## 🏆 Blockchain-Based Certificate Generation

### Generate Certificate
```http
POST /api/certificates/generate
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "achievement_type": "quiz_completion",
  "score": 85,
  "assessment_name": "TCS Aptitude Test"
}
```

**Response:**
```json
{
  "certificate_id": "cert_abc123def456",
  "blockchain_hash": "0x1234567890abcdef...",
  "pdf_path": "certificates/certificate_cert_abc123def456.pdf",
  "verification_url": "/api/certificates/verify/cert_abc123def456"
}
```

### Verify Certificate
```http
GET /api/certificates/verify/{certificate_id}
```

**Response:**
```json
{
  "valid": true,
  "certificate_data": {
    "certificate_id": "cert_abc123def456",
    "student_name": "John Doe",
    "student_email": "student@example.com",
    "achievement_type": "quiz_completion",
    "score": 85,
    "assessment_name": "TCS Aptitude Test",
    "issued_date": "2024-01-15T10:30:00Z",
    "issuer": "AI Placement Platform",
    "blockchain_hash": "0x1234567890abcdef..."
  },
  "blockchain_hash": "0x1234567890abcdef...",
  "verified_at": "2024-01-15T11:00:00Z"
}
```

---

## 👥 Community & Collaboration Features

### Get Challenges
```http
GET /api/community/challenges
```

**Parameters:**
- `type` (query): Challenge type (quiz, coding, debate)
- `difficulty` (query): Difficulty level (easy, medium, hard, all)

**Response:**
```json
{
  "challenges": [
    {
      "challenge_id": "challenge_123",
      "creator_email": "creator@example.com",
      "type": "quiz",
      "title": "Data Structures Challenge",
      "description": "Test your knowledge of data structures",
      "difficulty": "medium",
      "created_at": "2024-01-15T10:30:00Z",
      "participants": ["student1@example.com"],
      "status": "active",
      "max_participants": 10
    }
  ],
  "total": 1
}
```

### Create Challenge
```http
POST /api/community/create-challenge
```

**Request Body:**
```json
{
  "email": "creator@example.com",
  "type": "quiz",
  "title": "Algorithm Challenge",
  "description": "Test your algorithmic thinking",
  "difficulty": "hard",
  "questions": [
    {
      "id": 1,
      "question": "What is the time complexity of merge sort?",
      "options": ["O(n)", "O(n log n)", "O(n²)", "O(log n)"],
      "correct": 1
    }
  ],
  "max_participants": 5
}
```

### Get Leaderboard
```http
GET /api/community/leaderboard
```

**Parameters:**
- `type` (query): Leaderboard type (overall, company-specific)
- `period` (query): Time period (week, month, year, all)

**Response:**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "student_name": "John Doe",
      "email": "john@example.com",
      "branch": "Computer Science",
      "average_score": 92.5,
      "average_time": 150.2,
      "total_assessments": 25,
      "ranking_score": 95.8
    }
  ],
  "period": "month",
  "total_participants": 150
}
```

### Get Forum Posts
```http
GET /api/community/forums
```

**Parameters:**
- `category` (query): Post category (general, technical, career)
- `limit` (query): Number of posts to return (default: 20)

**Response:**
```json
{
  "posts": [
    {
      "post_id": "post_123",
      "author_email": "author@example.com",
      "title": "Best practices for coding interviews",
      "content": "Here are some tips for acing coding interviews...",
      "category": "technical",
      "created_at": "2024-01-15T10:30:00Z",
      "replies": [],
      "likes": 15,
      "sentiment": {
        "polarity": 0.8,
        "subjectivity": 0.6,
        "label": "positive"
      }
    }
  ],
  "total": 1
}
```

### Create Forum Post
```http
POST /api/community/create-post
```

**Request Body:**
```json
{
  "email": "author@example.com",
  "title": "Tips for System Design Interviews",
  "content": "System design interviews can be challenging...",
  "category": "technical"
}
```

**Response:**
```json
{
  "post_id": "post_456",
  "message": "Post created successfully",
  "moderation_confidence": 0.95
}
```

---

## 🔧 Existing Routes (Unchanged)

### Home
```http
GET /
```

### Student Signup
```http
POST /signup
```

### Verify OTP
```http
POST /verify_otp
```

### Student Login
```http
POST /login
```

---

## 📝 Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing or invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## 🔒 Security Notes

1. **Email Validation**: All endpoints validate email format and existence
2. **Rate Limiting**: Consider implementing rate limiting for production use
3. **Input Sanitization**: All user inputs are sanitized and validated
4. **Monitoring**: All activities are logged for security auditing
5. **Content Moderation**: Forum posts are automatically moderated using AI

---

## 🚀 Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment variables in `.env`
3. Run setup script: `python setup.py`
4. Start the application: `python app.py`
5. Test endpoints using the provided examples

For more detailed information, refer to `README_AI_FEATURES.md`.
