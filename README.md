# FASTAPI AUTH MODULE 

FastAPI application with JWT authentication, OAuth, and user management.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with the required environment variables:
```
DB_URL=postgresql://user:password@localhost/dbname
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
SMS_BEARER_TOKEN=your-sms-token
SMS_SENDER_ID=your-sender-id
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-password
SMTP_FROM_EMAIL=noreply@example.com
SMTP_USE_TLS=true
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URL=http://localhost:8000/auth/oauth/callback
SESSION_SECRET_KEY=your-session-secret-key
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`