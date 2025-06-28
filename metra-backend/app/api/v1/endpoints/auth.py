from datetime import timedelta
from typing import Any, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, User, UserUpdate, UserUsageStats, UserPublic, UserLogin
from app.services import auth as auth_service
import resend

router = APIRouter()

@router.post("/register", response_model=UserPublic)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """Register new user"""
    # 验证邀请码
    valid_invitation_codes = ["METRA2024", "EARLY2024", "BETA2024"]  # 有效的邀请码列表
    if user_in.invitation_code not in valid_invitation_codes:
        raise HTTPException(
            status_code=400,
            detail="Invalid invitation code. Registration requires a valid invitation code.",
        )
    
    user = await auth_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists.",
        )
    user = await auth_service.create_user(db, user_in)
    
    # Send welcome email (background task)
    if settings.RESEND_API_KEY:
        background_tasks.add_task(
            send_welcome_email, 
            user.email, 
            user.full_name
        )
    
    return user

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """OAuth2 compatible token login, accepting JSON."""
    user = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    await auth_service.update_last_login(db, user_id=user.id)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """Get current user"""
    return current_user

@router.put("/me", response_model=User)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """Update current user"""
    if user_in.email and user_in.email != current_user.email:
        existing = await auth_service.get_user_by_email(db, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
    
    # Update user fields
    if user_in.email:
        current_user.email = user_in.email
    if user_in.full_name is not None:
        current_user.full_name = user_in.full_name
    if user_in.password:
        current_user.hashed_password = auth_service.get_password_hash(user_in.password)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user

@router.get("/me/usage", response_model=UserUsageStats)
async def get_usage_stats(
    current_user: User = Depends(auth_service.get_current_active_user),
) -> Any:
    """Get current user's usage statistics"""
    return UserUsageStats(
        models_created_this_month=current_user.models_created_this_month,
        api_calls_this_month=current_user.api_calls_this_month,
        training_minutes_this_month=current_user.training_minutes_this_month,
        models_remaining=max(0, settings.FREE_MODELS_PER_MONTH - current_user.models_created_this_month),
        api_calls_remaining=max(0, settings.FREE_API_CALLS_PER_MONTH - current_user.api_calls_this_month),
        training_minutes_remaining=max(0, settings.FREE_TRAINING_MINUTES_PER_MONTH - current_user.training_minutes_this_month),
    )

@router.post("/forgot-password")
async def forgot_password(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Send password reset email"""
    user = await auth_service.get_user_by_email(db, email=email)
    if user:
        # Generate reset token
        reset_token = create_access_token(
            subject=str(user.id),
            expires_delta=timedelta(hours=1)
        )
        
        # Send reset email
        if settings.RESEND_API_KEY:
            background_tasks.add_task(
                send_reset_email,
                user.email,
                user.full_name,
                reset_token
            )
    
    # Always return success to prevent email enumeration
    return {"msg": "Password reset email sent if account exists"}

# Email helper functions
async def send_welcome_email(email: str, name: str):
    """Send welcome email to new user"""
    if not settings.RESEND_API_KEY:
        return
        
    resend.api_key = settings.RESEND_API_KEY
    
    params = {
        "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
        "to": [email],
        "subject": "Welcome to Metra - AI Training Made Simple",
        "html": f"""
        <h2>Welcome to Metra, {name or 'there'}!</h2>
        <p>Thank you for joining Metra. You're now ready to start training your own AI models without any coding!</p>
        <p>Here's what you can do with your free account:</p>
        <ul>
            <li>Create up to {settings.FREE_MODELS_PER_MONTH} AI models per month</li>
            <li>Make up to {settings.FREE_API_CALLS_PER_MONTH} API calls</li>
            <li>Use up to {settings.FREE_TRAINING_MINUTES_PER_MONTH} minutes of training time</li>
        </ul>
        <p>Get started by describing what kind of AI you want to build!</p>
        <br>
        <a href="https://metratraining.com/dashboard" style="background-color: #111827; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Go to Dashboard</a>
        """
    }
    
    try:
        resend.Emails.send(params)
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

async def send_reset_email(email: str, name: str, token: str):
    """Send password reset email"""
    if not settings.RESEND_API_KEY:
        return
        
    resend.api_key = settings.RESEND_API_KEY
    
    reset_link = f"https://metratraining.com/reset-password?token={token}"
    
    params = {
        "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
        "to": [email],
        "subject": "Reset Your Metra Password",
        "html": f"""
        <h2>Password Reset Request</h2>
        <p>Hi {name or 'there'},</p>
        <p>We received a request to reset your password. Click the link below to create a new password:</p>
        <br>
        <a href="{reset_link}" style="background-color: #111827; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">Reset Password</a>
        <br><br>
        <p>This link will expire in 1 hour. If you didn't request this, please ignore this email.</p>
        """
    }
    
    try:
        resend.Emails.send(params)
    except Exception as e:
        print(f"Failed to send reset email: {e}") 