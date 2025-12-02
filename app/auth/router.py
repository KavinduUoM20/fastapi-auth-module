import logging
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session
from app.users.schemas import UserCreate, UserLogin, UserOut, Token
from app.auth.service import register_user, authenticate_user, generate_token_for_user
from app.core.sms import send_sms
from app.core.email import send_email
from app.core.email_templates import get_email_template
from app.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut)
def register(
    user_data: UserCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        new_user = register_user(user_data, db)
        
        # Send welcome SMS in background
        if new_user.mobile_phone:
            welcome_message = f"Welcome {new_user.first_name or 'User'}! Your account has been successfully registered."
            background_tasks.add_task(send_sms, new_user.mobile_phone, welcome_message)
        
        # Send welcome email in background
        if new_user.email:
            user_name = new_user.first_name or "User"
            email_subject = "Welcome! Your account has been registered"
            email_body = f"Hello {user_name},\n\nWelcome! Your account has been successfully registered.\n\nThank you for joining us!"
            
            # Render HTML template
            try:
                email_html = get_email_template('welcome.html', user_name=user_name)
            except Exception as e:
                logger.error(f"Failed to render welcome email template: {e}")
                # Fallback to simple HTML if template fails
                email_html = f"""
                <html>
                    <body>
                        <h2>Welcome, {user_name}!</h2>
                        <p>Your account has been successfully registered.</p>
                        <p>Thank you for joining us!</p>
                    </body>
                </html>
                """
            
            background_tasks.add_task(send_email, new_user.email, email_subject, email_body, email_html)
        
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in register endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while registering user"
        )

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(user_data.email, user_data.password, db)
        token = generate_token_for_user(user)
        return Token(access_token=token)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while logging in"
        )