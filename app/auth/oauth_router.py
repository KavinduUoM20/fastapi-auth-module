import logging
from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import RedirectResponse, JSONResponse
from sqlmodel import Session
from authlib.integrations.starlette_client import OAuth, OAuthError

from app.core.config import settings
from app.auth.service import create_or_get_oauth_user, generate_token_for_user
from app.core.email import send_email
from app.core.email_templates import get_email_template
from app.session import get_db
from app.users.schemas import Token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

# Initialize OAuth
oauth = OAuth()

# Register Google OAuth
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        client_kwargs={
            'scope': 'email openid profile',
        }
    )

@router.get("/login/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth login flow.
    Redirects user to Google's authorization page.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured"
        )
    
    redirect_uri = request.url_for('oauth_callback')
    return await oauth.google.authorize_redirect(request, str(redirect_uri))

@router.get("/callback", name="oauth_callback")
async def oauth_callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from provider.
    Creates or retrieves user and returns JWT token.
    Sends welcome email if user is newly registered.
    """
    try:
        # Get access token from OAuth provider
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        logger.error(f"OAuth error: {e.error}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": f"OAuth error: {e.error}"}
        )
    except Exception as e:
        logger.error(f"Error during OAuth callback: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An error occurred during OAuth authentication"}
        )
    
    # Get user info from token
    user_info = token.get('userinfo')
    if not user_info:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": "User information not provided by OAuth provider"}
        )
    
    try:
        # Extract provider information
        provider = 'google'
        provider_id = user_info.get('sub')  # Google's unique user ID
        
        # Create or get user (returns user and is_new_user flag)
        user, is_new_user = create_or_get_oauth_user(user_info, provider, provider_id, db)
        
        # Send welcome email if this is a new registration
        if is_new_user and user.email:
            user_name = user.first_name or "User"
            email_subject = "Welcome! Your account has been registered"
            email_body = f"Hello {user_name},\n\nWelcome! Your account has been successfully registered via Google.\n\nThank you for joining us!"
            
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
                        <p>Your account has been successfully registered via Google.</p>
                        <p>Thank you for joining us!</p>
                    </body>
                </html>
                """
            
            background_tasks.add_task(send_email, user.email, email_subject, email_body, email_html)
        
        # Generate JWT token
        access_token = generate_token_for_user(user)
        
        # Return token (you can also redirect to a frontend URL with token)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "provider": user.provider
                }
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing OAuth user: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An error occurred while processing OAuth authentication"}
        )

