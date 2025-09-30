# Matrix Social Network

A minimalist Matrix-themed social network built with FastAPI and React.

## Features

✅ **User Authentication**
- Simple registration with username and password
- JWT-based authentication
- Secure password hashing with bcrypt

✅ **Wall Posts**
- Post status updates on your own wall
- View other users' walls
- Write messages on other users' walls
- Real-time post display with author attribution

✅ **User Discovery**
- Browse all registered users
- Navigate to any user's profile
- See who posted what and where

✅ **Matrix Theme**
- Dark background (#001200, #0d0208)
- Iconic Matrix green (#00ff41, #008f11)
- Animated digital rain effect
- Matrix-style typography and UI elements

## API Endpoints

### Authentication
- `POST /api/register` - Create a new user account
- `POST /api/login` - Authenticate and get JWT token

### Posts
- `POST /api/posts` - Create a post (requires auth)
- `GET /api/posts/{username}` - Get all posts on a user's wall

### Users
- `GET /api/users` - List all users

## Database Schema

### Users Collection
```json
{
  "_id": "uuid",
  "username": "string (unique)",
  "password": "string (hashed)",
  "created_at": "datetime"
}
```

### Posts Collection
```json
{
  "id": "uuid",
  "wall_owner": "username",
  "author": "username",
  "content": "string",
  "created_at": "datetime"
}
```

## User Flow

1. **Registration/Login** - Users start at `/` and can register or login
2. **Profile** - After login, redirected to `/profile/{username}` to see their wall
3. **Post Status** - Users can post on their own wall or others' walls
4. **Discover Users** - Click "Users" to browse all users in `/users`
5. **Visit Walls** - Click any username to visit their profile and post on their wall

## Technical Stack

### Backend
- FastAPI with async/await support
- MongoDB with Motor (async driver)
- JWT authentication with PyJWT
- bcrypt for password hashing

### Frontend
- React 19
- React Router v7
- shadcn/ui components
- Tailwind CSS
- Custom Matrix rain animation

## Testing

All API endpoints have been tested:
```bash
cd backend
python tests/test_matrix_api.py
```

Tests verify:
- User registration and login
- JWT token generation
- Wall post creation
- Cross-user posting
- User listing
- Duplicate registration prevention

## Running the Application

The application is already running with supervisor:
- Backend: `sudo supervisorctl restart backend`
- Frontend: `sudo supervisorctl restart frontend`

Backend is accessible at: http://localhost:8001
Frontend is accessible at: http://localhost:3000

## Acceptance Criteria - Status

✅ Users can register with username/password
✅ Users can login and receive JWT token
✅ Users can post status on their own wall
✅ Users can view other users' profiles
✅ Users can post messages on other users' walls
✅ Matrix theme applied throughout (dark bg, green text, digital rain)

## Matrix Theme Elements

1. **Colors**
   - Background: Dark green-black (#001200)
   - Primary text: Bright Matrix green (#00ff41)
   - Secondary text: Darker green (#008f11)

2. **Visual Effects**
   - Animated digital rain falling in background
   - Green glowing borders on cards
   - Matrix-style monospace fonts
   - Cyberpunk aesthetic throughout

3. **UI Components**
   - Custom Matrix-themed buttons with green glow
   - Avatar circles with green borders
   - Cards with subtle green shadows
   - Input fields with green focus rings

Welcome to the Matrix. 🟢