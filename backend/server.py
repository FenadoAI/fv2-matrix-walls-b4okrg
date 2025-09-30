"""FastAPI server exposing AI agent endpoints."""

import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

from ai_agents.agents import AgentConfig, ChatAgent, SearchAgent


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).parent

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "matrix-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()


# Auth Models
class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Post Models
class PostCreate(BaseModel):
    wall_owner: str
    content: str


class Post(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    wall_owner: str
    author: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StatusCheckCreate(BaseModel):
    client_name: str


class ChatRequest(BaseModel):
    message: str
    agent_type: str = "chat"
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    response: str
    agent_type: str
    capabilities: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    max_results: int = 5


class SearchResponse(BaseModel):
    success: bool
    query: str
    summary: str
    search_results: Optional[dict] = None
    sources_count: int
    error: Optional[str] = None


def _ensure_db(request: Request):
    try:
        return request.app.state.db
    except AttributeError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=503, detail="Database not ready") from exc


def _get_agent_cache(request: Request) -> Dict[str, object]:
    if not hasattr(request.app.state, "agent_cache"):
        request.app.state.agent_cache = {}
    return request.app.state.agent_cache


async def _get_or_create_agent(request: Request, agent_type: str):
    cache = _get_agent_cache(request)
    if agent_type in cache:
        return cache[agent_type]

    config: AgentConfig = request.app.state.agent_config

    if agent_type == "search":
        cache[agent_type] = SearchAgent(config)
    elif agent_type == "chat":
        cache[agent_type] = ChatAgent(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown agent type '{agent_type}'")

    return cache[agent_type]


# Auth Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)):
    db = _ensure_db(request)
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(ROOT_DIR / ".env")

    mongo_url = os.getenv("MONGO_URL")
    db_name = os.getenv("DB_NAME")

    if not mongo_url or not db_name:
        missing = [name for name, value in {"MONGO_URL": mongo_url, "DB_NAME": db_name}.items() if not value]
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    client = AsyncIOMotorClient(mongo_url)

    try:
        app.state.mongo_client = client
        app.state.db = client[db_name]
        app.state.agent_config = AgentConfig()
        app.state.agent_cache = {}
        logger.info("AI Agents API starting up")
        yield
    finally:
        client.close()
        logger.info("AI Agents API shutdown complete")


app = FastAPI(
    title="AI Agents API",
    description="Minimal AI Agents API with LangGraph and MCP support",
    lifespan=lifespan,
)

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"message": "Welcome to the Matrix"}


# Authentication Endpoints
@api_router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, request: Request):
    db = _ensure_db(request)

    # Check if username exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user_id = str(uuid.uuid4())
    hashed_pw = hash_password(user_data.password)
    user = {
        "_id": user_id,
        "username": user_data.username,
        "password": hashed_pw,
        "created_at": datetime.now(timezone.utc),
    }

    await db.users.insert_one(user)

    # Create access token
    access_token = create_access_token(data={"sub": user_data.username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user_id, username=user_data.username, created_at=user["created_at"]),
    )


@api_router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    db = _ensure_db(request)

    user = await db.users.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": user["username"]})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(id=user["_id"], username=user["username"], created_at=user["created_at"]),
    )


# Wall Post Endpoints
@api_router.post("/posts", response_model=Post)
async def create_post(post_data: PostCreate, request: Request, current_user: dict = Depends(get_current_user)):
    db = _ensure_db(request)

    # Verify wall owner exists
    wall_owner_user = await db.users.find_one({"username": post_data.wall_owner})
    if not wall_owner_user:
        raise HTTPException(status_code=404, detail="Wall owner not found")

    # Create post
    post = Post(
        wall_owner=post_data.wall_owner,
        author=current_user["username"],
        content=post_data.content,
    )

    await db.posts.insert_one(post.model_dump())

    return post


@api_router.get("/posts/{username}", response_model=List[Post])
async def get_user_posts(username: str, request: Request):
    db = _ensure_db(request)

    # Verify user exists
    user = await db.users.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get all posts for this wall
    posts = await db.posts.find({"wall_owner": username}).sort("created_at", -1).to_list(1000)

    return [Post(**post) for post in posts]


@api_router.get("/users", response_model=List[UserResponse])
async def get_users(request: Request):
    db = _ensure_db(request)

    users = await db.users.find().to_list(1000)
    return [UserResponse(id=user["_id"], username=user["username"], created_at=user["created_at"]) for user in users]


@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate, request: Request):
    db = _ensure_db(request)
    status_obj = StatusCheck(**input.model_dump())
    await db.status_checks.insert_one(status_obj.model_dump())
    return status_obj


@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks(request: Request):
    db = _ensure_db(request)
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]


@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(chat_request: ChatRequest, request: Request):
    try:
        agent = await _get_or_create_agent(request, chat_request.agent_type)
        response = await agent.execute(chat_request.message)

        return ChatResponse(
            success=response.success,
            response=response.content,
            agent_type=chat_request.agent_type,
            capabilities=agent.get_capabilities(),
            metadata=response.metadata,
            error=response.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in chat endpoint")
        return ChatResponse(
            success=False,
            response="",
            agent_type=chat_request.agent_type,
            capabilities=[],
            error=str(exc),
        )


@api_router.post("/search", response_model=SearchResponse)
async def search_and_summarize(search_request: SearchRequest, request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        search_prompt = (
            f"Search for information about: {search_request.query}. "
            "Provide a comprehensive summary with key findings."
        )
        result = await search_agent.execute(search_prompt, use_tools=True)

        if result.success:
            metadata = result.metadata or {}
            return SearchResponse(
                success=True,
                query=search_request.query,
                summary=result.content,
                search_results=metadata,
                sources_count=int(metadata.get("tool_run_count", metadata.get("tools_used", 0)) or 0),
            )

        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=result.error,
        )
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error in search endpoint")
        return SearchResponse(
            success=False,
            query=search_request.query,
            summary="",
            sources_count=0,
            error=str(exc),
        )


@api_router.get("/agents/capabilities")
async def get_agent_capabilities(request: Request):
    try:
        search_agent = await _get_or_create_agent(request, "search")
        chat_agent = await _get_or_create_agent(request, "chat")

        return {
            "success": True,
            "capabilities": {
                "search_agent": search_agent.get_capabilities(),
                "chat_agent": chat_agent.get_capabilities(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Error getting capabilities")
        return {"success": False, "error": str(exc)}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
