# 第一阶段开发指南 - 用户认证系统

> 👋 欢迎接手 Metra 项目！本文档将指导你完成第一阶段的开发任务。

## 📋 任务概览

**阶段目标**：实现完整的用户认证系统  
**预计时间**：2-3天  
**技术栈**：Supabase Auth + FastAPI + React

---

## 🎯 第一阶段任务清单

### 后端任务
- [ ] 完善用户模型和数据库表
- [ ] 实现注册、登录、登出 API
- [ ] 添加 JWT Token 验证中间件
- [ ] 实现用户信息获取和更新 API
- [ ] 添加密码重置功能
- [ ] 配置 Supabase Auth 集成

### 前端任务
- [ ] 创建注册页面
- [ ] 创建登录页面
- [ ] 实现认证状态管理
- [ ] 添加路由守卫
- [ ] 创建用户 Profile 页面
- [ ] 实现自动 Token 刷新

---

## 🚀 开始前的准备

### 1. 环境设置
```bash
# 1. 进入项目目录
cd /Users/jz/Desktop/Metra

# 2. 运行环境设置脚本
./setup-dev.sh

# 3. 启动开发服务器（需要3个终端）
# Terminal 1 - 后端
./start-backend.sh

# Terminal 2 - 前端  
./start-frontend.sh

# Terminal 3 - Inngest（这阶段可选）
./start-inngest.sh
```

### 2. 验证环境
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs
- 前端: http://localhost:5173

---

## 📝 详细实现步骤

### Step 1: 后端 - 创建用户模型

#### 1.1 创建 SQLAlchemy 模型
创建文件 `metra-backend/app/models/user.py`:

```python
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Free tier limits
    models_created_this_month = Column(Integer, default=0)
    api_calls_this_month = Column(Integer, default=0)
    training_minutes_this_month = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True))
    
    # Subscription info (for future)
    subscription_tier = Column(String, default="free")
    subscription_expires_at = Column(DateTime(timezone=True))
```

#### 1.2 创建 Pydantic Schemas
创建文件 `metra-backend/app/schemas/user.py`:

```python
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, UUID4

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: str

class UserUsageStats(BaseModel):
    models_created_this_month: int
    api_calls_this_month: int
    training_minutes_this_month: int
    models_remaining: int
    api_calls_remaining: int
    training_minutes_remaining: int
```

#### 1.3 创建认证服务
创建文件 `metra-backend/app/services/auth.py`:

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.db.base import get_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
        full_name=user_create.full_name
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def authenticate_user(
    db: AsyncSession, 
    email: str, 
    password: str
) -> Optional[User]:
    user = await get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    await db.commit()
    
    return user

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
```

#### 1.4 创建认证工具函数
创建文件 `metra-backend/app/core/security.py`:

```python
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from app.core.config import settings

def create_access_token(
    subject: Union[str, Any], 
    expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt
```

#### 1.5 创建 Token Schema
创建文件 `metra-backend/app/schemas/token.py`:

```python
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
```

### Step 2: 后端 - 实现 API 端点

#### 2.1 更新认证路由
更新 `metra-backend/app/api/v1/endpoints/auth.py`（已有基础代码）:

```python
from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import EmailStr

from app.core.config import settings
from app.core.security import create_access_token
from app.db.base import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, User, UserUpdate, UserUsageStats
from app.services import auth as auth_service
import resend

router = APIRouter()

@router.post("/register", response_model=User)
async def register(
    *,
    db: AsyncSession = Depends(get_db),
    user_in: UserCreate,
    background_tasks: BackgroundTasks
) -> Any:
    """Register new user"""
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
async def login(
    db: AsyncSession = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login"""
    user = await auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id), expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }

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
```

### Step 3: 前端 - 实现认证界面

#### 3.1 安装认证相关依赖
```bash
cd metra-ai-factory-main
npm install @supabase/supabase-js zustand
```

#### 3.2 创建 Supabase 客户端
创建文件 `metra-ai-factory-main/src/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

#### 3.3 创建认证状态管理
创建文件 `metra-ai-factory-main/src/stores/authStore.ts`:

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  full_name?: string
  is_active: boolean
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  setUser: (user: User | null) => void
  setToken: (token: string | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      setLoading: (loading) => set({ isLoading: loading }),
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        user: state.user, 
        token: state.token 
      }),
    }
  )
)
```

#### 3.4 创建 API 客户端
创建文件 `metra-ai-factory-main/src/lib/api.ts`:

```typescript
import { useAuthStore } from '@/stores/authStore'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = useAuthStore.getState().token
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    
    return headers
  }

  async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...options.headers,
      },
    })

    if (response.status === 401) {
      // Token expired or invalid
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Something went wrong')
    }

    return response.json()
  }

  // Auth endpoints
  async register(email: string, password: string, fullName?: string) {
    return this.request<User>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    })
  }

  async login(email: string, password: string) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Login failed')
    }

    return response.json()
  }

  async getMe() {
    return this.request<User>('/auth/me')
  }

  async updateMe(data: { email?: string; full_name?: string; password?: string }) {
    return this.request<User>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getUsageStats() {
    return this.request('/auth/me/usage')
  }

  async forgotPassword(email: string) {
    return this.request('/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  }
}

export const api = new ApiClient()
```

#### 3.5 创建登录页面
创建文件 `metra-ai-factory-main/src/pages/Login.tsx`:

```tsx
import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function Login() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)
  const { setUser, setToken } = useAuthStore()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true)
    try {
      const response = await api.login(data.email, data.password)
      setToken(response.access_token)
      
      // Get user info
      const user = await api.getMe()
      setUser(user)
      
      toast({
        title: 'Welcome back!',
        description: 'You have successfully logged in.',
      })
      
      navigate('/dashboard')
    } catch (error) {
      toast({
        title: 'Login failed',
        description: error instanceof Error ? error.message : 'Please check your credentials',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Welcome back
          </CardTitle>
          <CardDescription className="text-center">
            Enter your email and password to login
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                {...register('email')}
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                {...register('password')}
                disabled={isLoading}
              />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                'Login'
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <Link
            to="/forgot-password"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Forgot your password?
          </Link>
          <div className="text-sm text-gray-600">
            Don't have an account?{' '}
            <Link to="/register" className="text-gray-900 font-medium hover:underline">
              Sign up
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
```

#### 3.6 创建注册页面
创建文件 `metra-ai-factory-main/src/pages/Register.tsx`:

```tsx
import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'

const registerSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  confirmPassword: z.string(),
  fullName: z.string().optional(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})

type RegisterForm = z.infer<typeof registerSchema>

export default function Register() {
  const navigate = useNavigate()
  const { toast } = useToast()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegisterForm>({
    resolver: zodResolver(registerSchema),
  })

  const onSubmit = async (data: RegisterForm) => {
    setIsLoading(true)
    try {
      await api.register(data.email, data.password, data.fullName)
      
      toast({
        title: 'Account created!',
        description: 'Please login with your new account.',
      })
      
      navigate('/login')
    } catch (error) {
      toast({
        title: 'Registration failed',
        description: error instanceof Error ? error.message : 'Something went wrong',
        variant: 'destructive',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            Create an account
          </CardTitle>
          <CardDescription className="text-center">
            Start training your own AI models in minutes
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name (optional)</Label>
              <Input
                id="fullName"
                placeholder="John Doe"
                {...register('fullName')}
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                {...register('email')}
                disabled={isLoading}
              />
              {errors.email && (
                <p className="text-sm text-red-500">{errors.email.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                {...register('password')}
                disabled={isLoading}
              />
              {errors.password && (
                <p className="text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                {...register('confirmPassword')}
                disabled={isLoading}
              />
              {errors.confirmPassword && (
                <p className="text-sm text-red-500">{errors.confirmPassword.message}</p>
              )}
            </div>
            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create account'
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter>
          <div className="text-sm text-gray-600 text-center w-full">
            Already have an account?{' '}
            <Link to="/login" className="text-gray-900 font-medium hover:underline">
              Login
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
```

#### 3.7 创建路由守卫
创建文件 `metra-ai-factory-main/src/components/ProtectedRoute.tsx`:

```tsx
import { Navigate } from 'react-router-dom'
import { useAuthStore } from '@/stores/authStore'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { user, token } = useAuthStore()

  if (!user || !token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}
```

#### 3.8 更新路由配置
更新 `metra-ai-factory-main/src/App.tsx`:

```tsx
import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { api } from '@/lib/api'

// Pages
import Index from '@/pages/Index'
import Dashboard from '@/pages/Dashboard'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import NotFound from '@/pages/NotFound'

// Components
import ProtectedRoute from '@/components/ProtectedRoute'
import { Toaster } from '@/components/ui/toaster'

function App() {
  const { token, setUser, setToken } = useAuthStore()

  useEffect(() => {
    // Check if user is logged in on app load
    const checkAuth = async () => {
      if (token) {
        try {
          const user = await api.getMe()
          setUser(user)
        } catch (error) {
          // Token is invalid
          setToken(null)
          setUser(null)
        }
      }
    }
    
    checkAuth()
  }, [])

  return (
    <>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Index />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        
        {/* 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
      
      <Toaster />
    </>
  )
}

export default App
```

### Step 4: 测试和验证

#### 4.1 测试后端 API
使用 http://localhost:8000/docs 测试以下端点：
- POST `/api/v1/auth/register` - 注册新用户
- POST `/api/v1/auth/login` - 用户登录
- GET `/api/v1/auth/me` - 获取当前用户信息
- PUT `/api/v1/auth/me` - 更新用户信息
- GET `/api/v1/auth/me/usage` - 获取使用统计

#### 4.2 测试前端流程
1. 访问 http://localhost:5173/register 注册新账号
2. 登录后应该跳转到 Dashboard
3. 刷新页面应该保持登录状态
4. 尝试访问 Dashboard 而不登录应该跳转到登录页

#### 4.3 创建数据库迁移
```bash
cd metra-backend
alembic revision --autogenerate -m "Add user model"
alembic upgrade head
```

---

## 📝 交付清单

完成第一阶段后，请确保：

### 后端
- [ ] 用户模型已创建并迁移到数据库
- [ ] 所有认证 API 端点正常工作
- [ ] JWT Token 验证中间件正常工作
- [ ] 邮件发送功能已配置（如果有 Resend API Key）

### 前端
- [ ] 登录页面功能正常
- [ ] 注册页面功能正常
- [ ] 认证状态持久化（刷新不丢失）
- [ ] 路由守卫正常工作
- [ ] Token 自动添加到 API 请求

### 测试
- [ ] 可以成功注册新用户
- [ ] 可以成功登录
- [ ] Token 过期后自动跳转登录
- [ ] 用户信息更新功能正常

---

## 🎯 下一阶段预告

第二阶段将实现 **Prompt-to-Schema 对话系统**：
- 多轮对话界面
- GPT-4 集成
- 任务结构化生成
- Schema 预览和编辑

---

## 📞 需要帮助？

- 查看 [开发手册](./Metra_Development_Manual.md)
- 查看 [API Keys 清单](./API_KEYS_CHECKLIST.md)
- 检查环境变量是否正确配置

祝开发顺利！🚀 