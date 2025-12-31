# Database API Documentation - Comprehensive Quiz Management

## Overview
This document describes the comprehensive database API endpoints for managing quiz data, student responses, scores, and analytics in the AI-Powered Placement Platform.

## Base URL
```
http://localhost:5000
```

---

## 🗄️ Database Collections

### Core Collections:
- **students** - Student profiles and basic information
- **quizzes** - Quiz questions and metadata
- **quiz_attempts** - Quiz attempt sessions and results
- **student_responses** - Individual question responses
- **performance_analytics** - Aggregated performance data
- **quiz_statistics** - Quiz-level statistics
- **student_progress** - Student progress tracking
- **leaderboard** - Ranking and leaderboard data

---

## 📝 Quiz Management Endpoints

### Create Quiz
```http
POST /api/quiz/create
```

**Request Body:**
```json
{
  "quiz_data": {
    "quiz_id": "tcs_aptitude_basic_001",
    "company": "tcs",
    "type": "aptitude",
    "title": "TCS Aptitude Test - Basic Level",
    "description": "Basic aptitude questions for TCS placement preparation",
    "questions": [
      {
        "question_id": "q1",
        "question": "What is the output of: int x = 5; System.out.println(x++ + ++x);",
        "options": ["10", "11", "12", "13"],
        "correct_answer": 2,
        "explanation": "x++ returns 5 then increments to 6, ++x increments to 7 then returns 7, so 5+7=12",
        "difficulty": 0.7,
        "topic": "Java Basics",
        "time_limit": 60,
        "points": 1
      }
    ],
    "total_time_limit": 1800,
    "difficulty_level": "medium",
    "created_by": "admin"
  }
}
```

**Response:**
```json
{
  "message": "Quiz created successfully",
  "quiz_id": "ObjectId('...')",
  "quiz_data": { /* quiz data */ }
}
```

### Start Quiz Attempt
```http
POST /api/quiz/{quiz_id}/start
```

**Request Body:**
```json
{
  "email": "student@example.com",
  "device_info": {
    "browser": "Chrome",
    "os": "Windows",
    "ip_address": "192.168.1.1"
  }
}
```

**Response:**
```json
{
  "attempt_id": "attempt_123456789",
  "quiz_data": {
    "quiz_id": "tcs_aptitude_basic_001",
    "title": "TCS Aptitude Test - Basic Level",
    "questions": [ /* questions array */ ],
    "total_time_limit": 1800
  },
  "message": "Quiz started successfully"
}
```

### Submit Quiz Answer
```http
POST /api/quiz/attempt/{attempt_id}/submit-answer
```

**Request Body:**
```json
{
  "question_id": "q1",
  "selected_answer": 2,
  "response_time": 45
}
```

**Response:**
```json
{
  "message": "Answer submitted successfully"
}
```

### Complete Quiz
```http
POST /api/quiz/attempt/{attempt_id}/complete
```

**Request Body:**
```json
{
  "behavior_data": {
    "tab_switches": 2,
    "fullscreen_exits": 0,
    "copy_paste_attempts": 0,
    "right_clicks": 1,
    "suspicious_activities": []
  }
}
```

**Response:**
```json
{
  "message": "Quiz completed successfully",
  "results": {
    "attempt": {
      "attempt_id": "attempt_123456789",
      "student_email": "student@example.com",
      "score": 3,
      "max_score": 3,
      "percentage": 100,
      "time_taken": 165,
      "correct_answers": 3,
      "incorrect_answers": 0
    },
    "responses": [
      {
        "question_id": "q1",
        "selected_answer": 2,
        "correct_answer": 2,
        "is_correct": true,
        "response_time": 45,
        "points_earned": 1
      }
    ],
    "quiz_details": { /* quiz information */ }
  }
}
```

---

## 📊 Analytics & Reporting Endpoints

### Get Quiz Statistics
```http
GET /api/quiz/{quiz_id}/statistics
```

**Response:**
```json
{
  "quiz_id": "tcs_aptitude_basic_001",
  "statistics": {
    "total_attempts": 150,
    "total_students": 120,
    "average_score": 72.5,
    "highest_score": 95.0,
    "lowest_score": 25.0,
    "completion_rate": 85.0,
    "average_time_taken": 2800,
    "calculated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Student Performance
```http
GET /api/student/{email}/performance?company=tcs
```

**Response:**
```json
{
  "student_email": "student@example.com",
  "performance_data": [
    {
      "company": "tcs",
      "total_attempts": 5,
      "total_questions": 25,
      "correct_answers": 20,
      "average_score": 80.0,
      "average_response_time": 45.5,
      "improvement_trend": "improving",
      "strengths": ["Java Basics"],
      "weaknesses": ["Algorithms"],
      "calculated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

### Get Student Quiz History
```http
GET /api/student/{email}/quiz-history?limit=20
```

**Response:**
```json
{
  "student_email": "student@example.com",
  "quiz_history": [
    {
      "attempt_id": "attempt_123456789",
      "quiz_id": "tcs_aptitude_basic_001",
      "company": "tcs",
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:30:00Z",
      "score": 3,
      "percentage": 100,
      "time_taken": 1800,
      "status": "completed"
    }
  ],
  "total_attempts": 15
}
```

### Get Leaderboard
```http
GET /api/leaderboard?company=tcs&limit=50
```

**Response:**
```json
{
  "leaderboard": [
    {
      "student_email": "john.doe@example.com",
      "student_name": "John Doe",
      "branch": "Computer Science",
      "company": "tcs",
      "average_score": 95.0,
      "total_attempts": 10,
      "total_questions": 50,
      "correct_answers": 47
    }
  ],
  "company": "tcs",
  "limit": 50
}
```

### Get Company Performance Summary
```http
GET /api/company/{company}/performance-summary
```

**Response:**
```json
{
  "company": "tcs",
  "summary": {
    "total_students": 120,
    "total_attempts": 450,
    "total_questions": 2250,
    "average_score": 72.5,
    "completion_rate": 85.0,
    "generated_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Quiz Attempt Details
```http
GET /api/quiz/attempt/{attempt_id}/details
```

**Response:**
```json
{
  "attempt_id": "attempt_123456789",
  "details": {
    "attempt": {
      "attempt_id": "attempt_123456789",
      "student_email": "student@example.com",
      "quiz_id": "tcs_aptitude_basic_001",
      "score": 3,
      "percentage": 100,
      "time_taken": 165,
      "behavior_data": { /* behavior tracking data */ },
      "device_info": { /* device information */ }
    },
    "responses": [
      {
        "question_id": "q1",
        "selected_answer": 2,
        "correct_answer": 2,
        "is_correct": true,
        "response_time": 45,
        "answered_at": "2024-01-15T10:15:00Z"
      }
    ],
    "quiz_details": { /* complete quiz information */ }
  }
}
```

---

## 🧪 Testing the Database

### Initialize Database with Sample Data
```bash
python init_database.py
```

This script will:
- Create database collections and indexes
- Insert sample students and quizzes
- Test all database operations
- Verify data integrity

### Sample Test Flow

1. **Create a student:**
```bash
curl -X POST "http://localhost:5000/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Student",
    "branch": "Computer Science",
    "email": "test@example.com",
    "year": "2024"
  }'
```

2. **Start a quiz:**
```bash
curl -X POST "http://localhost:5000/api/quiz/tcs_aptitude_basic_001/start" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "device_info": {
      "browser": "Chrome",
      "os": "Windows"
    }
  }'
```

3. **Submit answers:**
```bash
curl -X POST "http://localhost:5000/api/quiz/attempt/{attempt_id}/submit-answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "q1",
    "selected_answer": 2,
    "response_time": 45
  }'
```

4. **Complete quiz:**
```bash
curl -X POST "http://localhost:5000/api/quiz/attempt/{attempt_id}/complete" \
  -H "Content-Type: application/json" \
  -d '{
    "behavior_data": {
      "tab_switches": 0,
      "fullscreen_exits": 0
    }
  }'
```

5. **View results:**
```bash
curl "http://localhost:5000/api/student/test@example.com/performance"
```

---

## 📈 Data Analytics Features

### Performance Metrics Tracked:
- **Individual Performance:**
  - Quiz scores and percentages
  - Response times per question
  - Improvement trends over time
  - Strengths and weaknesses by topic

- **Quiz Analytics:**
  - Overall difficulty rating
  - Question-level statistics
  - Completion rates
  - Average scores and time taken

- **Company Analytics:**
  - Performance by company
  - Student engagement metrics
  - Success rates by difficulty level

### Real-time Monitoring:
- Cheating detection through behavioral analysis
- Suspicious activity logging
- Performance tracking and alerts
- Automated insights generation

---

## 🔒 Security Features

### Data Protection:
- Input validation and sanitization
- Secure session management
- Behavioral monitoring and logging
- Encrypted sensitive data storage

### Cheating Prevention:
- Tab switch detection
- Copy-paste monitoring
- Time pattern analysis
- Suspicious behavior flagging

---

## 🚀 Getting Started

1. **Set up environment:**
```bash
# Copy environment template
cp env_example.txt .env

# Configure your MongoDB URI and other settings
```

2. **Initialize database:**
```bash
python init_database.py
```

3. **Start the application:**
```bash
python app.py
```

4. **Test endpoints:**
Use the sample requests provided above or refer to the Postman collection.

---

## 📞 Support

For technical support or questions about the database API:
- Check the main API documentation: `API_DOCUMENTATION.md`
- Review the database schema: `database_schema.py`
- Test with sample data: `init_database.py`
