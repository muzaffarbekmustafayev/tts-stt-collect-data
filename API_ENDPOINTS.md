# API Endpoints Documentation

Base URL: `http://localhost:8000`

## Authentication

### Login
- **POST** `/auth/login`
- **Body**: `{ "username": "string", "password": "string" }`
- **Response**: `{ "access_token": "string", "token_type": "bearer" }`

## Admin Endpoints

All admin endpoints require authentication with Bearer token.

### Admin Users

#### Get All Admin Users
- **GET** `/admin/admin-users?page=1&limit=20`
- **Auth**: Required (Admin/SuperAdmin)
- **Response**: Array of admin users

#### Create Admin User
- **POST** `/admin/`
- **Auth**: Required (SuperAdmin only)
- **Body**: `{ "username": "string", "password": "string", "role": "admin|checker|superadmin", "is_active": true }`

#### Update Admin User
- **PUT** `/admin/{id}`
- **Auth**: Required (SuperAdmin only)
- **Body**: `{ "username": "string", "password": "string", "role": "string", "is_active": boolean }`

#### Delete Admin User
- **DELETE** `/admin/{id}`
- **Auth**: Required (SuperAdmin only)

### Users

#### Get All Users
- **GET** `/admin/users?page=1&limit=20&name=search`
- **Auth**: Required (Admin)
- **Query Params**:
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
  - `name`: Search by name (optional)

#### Update User
- **PUT** `/admin/users/{id}`
- **Auth**: Required (Admin)
- **Body**: `{ "telegram_id": "string", "name": "string", "gender": "string", "age": number, "info": "string" }`

#### Delete User
- **DELETE** `/admin/users/{id}`
- **Auth**: Required (Admin)

### Sentences

#### Get All Sentences
- **GET** `/admin/sentences?page=1&limit=20&text=search`
- **Auth**: Required (Admin)
- **Query Params**:
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
  - `text`: Search by text (optional)

### Received Audios

#### Get All Audios
- **GET** `/admin/audios?page=1&limit=20&status=pending&user_id=xxx&sentence_id=xxx`
- **Auth**: Required (Admin)
- **Query Params**:
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
  - `status`: Filter by status: "pending" or "approved" (optional)
  - `user_id`: Filter by user ID (optional)
  - `sentence_id`: Filter by sentence ID (optional)
- **Response**:
```json
{
  "data": [
    {
      "id": "string",
      "audio_path": "audio/filename.ogg",
      "duration": 12.5,
      "status": "pending|approved",
      "created_at": "2024-01-01T00:00:00Z",
      "sentence": "Text of sentence",
      "sentence_id": "string",
      "user_name": "User Name",
      "user_id": "string",
      "user_telegram_id": "123456789",
      "user_gender": "male|female",
      "user_age": 25
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

#### Get Audio by ID
- **GET** `/admin/audios/{id}`
- **Auth**: Required (Admin)
- **Response**: Single audio object with full details

#### Update Audio
- **PUT** `/admin/audios/{id}`
- **Auth**: Required (Admin)
- **Body**: `{ "status": "pending|approved", "audio_path": "string", "sentence_id": "string", "user_id": "string" }`

#### Delete Audio
- **DELETE** `/admin/audios/{id}`
- **Auth**: Required (Admin)
- **Note**: Cannot delete audio that has been checked

### Checked Audios

#### Get All Checked Audios
- **GET** `/admin/checked-audios?page=1&limit=20&status=approved&is_correct=true&checked_by_id=xxx`
- **Auth**: Required (Admin)
- **Query Params**:
  - `page`: Page number (default: 1)
  - `limit`: Items per page (default: 20)
  - `status`: Filter by status (optional)
  - `is_correct`: Filter by correctness (optional)
  - `checked_by_id`: Filter by checker ID (optional)
- **Response**:
```json
{
  "data": [
    {
      "id": "string",
      "audio_id": "string",
      "audio_path": "audio/filename.ogg",
      "audio_duration": 12.5,
      "sentence": "Text of sentence",
      "sentence_id": "string",
      "user_name": "User Name",
      "user_id": "string",
      "checked_by_id": "string",
      "checked_by_name": "Admin Username",
      "comment": "Optional comment",
      "is_correct": true,
      "status": "pending|approved",
      "checked_at": "2024-01-01T00:00:00Z",
      "second_checker_id": "string",
      "second_check_result": true,
      "second_checked_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

#### Get Checked Audio by ID
- **GET** `/admin/checked-audios/{id}`
- **Auth**: Required (Admin)
- **Response**: Single checked audio object with full details

#### Delete Checked Audio
- **DELETE** `/admin/checked-audios/{id}`
- **Auth**: Required (Admin)

### Statistics

#### Get Dashboard Statistics
- **GET** `/admin/statistics`
- **Auth**: Required (Admin)
- **Response**:
```json
{
  "statistics": {
    "users": 100,
    "sentences": 500,
    "audios": 1000,
    "approved_audios": 800,
    "pending_audios": 200,
    "checked_audios": 750,
    "admins": 5,
    "total_audio_duration_minutes": 1234.56,
    "total_audio_duration_hours": 20.58
  },
  "users": [...],
  "sentences": [...],
  "audios": [...],
  "checked_audios": [...],
  "admin_users": [...],
  "current_admin": {
    "id": "string",
    "username": "string",
    "role": "string",
    "is_active": true
  }
}
```

## Public Endpoints

### Users

#### Get User by Telegram ID
- **GET** `/users/{telegram_id}`
- **Response**: User object

#### Get User by ID
- **GET** `/users/by-id/{id}`
- **Response**: User object

#### Create User
- **POST** `/users/`
- **Body**: `{ "telegram_id": "string", "name": "string", "gender": "string", "age": number, "info": "string" }`

#### Update User
- **PUT** `/users/{id}`
- **Body**: User data

### Received Audio

#### Upload Audio
- **POST** `/received-audio/`
- **Form Data**:
  - `user_id`: User ID
  - `sentence_id`: Sentence ID
  - `file`: Audio file (multipart/form-data)

#### Get Audio for Checking
- **GET** `/received-audio/{user_id}`
- **Response**: Audio object for user to check

#### Get Audio by ID
- **GET** `/received-audio/by-id/{id}`
- **Response**: Audio object

### Checked Audio

#### Submit Audio Check
- **POST** `/checked-audio/`
- **Body**: `{ "checked_by": "user_id", "audio_id": "string", "is_correct": boolean, "comment": "string" }`

#### Get Checks by Audio
- **GET** `/checked-audio/by-audio/{audio_id}`
- **Response**: Array of check records for the audio

### Statistics

#### Get Public Statistics
- **GET** `/statistic/`
- **Response**: Public statistics

#### Get Statistics by Users
- **GET** `/statistic/by-users?page=1&limit=20&name=search`
- **Response**: User statistics with pagination

#### Get User's Audios
- **GET** `/statistic/by-users/audios?user_id=xxx&telegram_id=xxx`
- **Query Params**:
  - `user_id`: User ID (optional)
  - `telegram_id`: Telegram ID (optional)
  - Note: At least one parameter is required

### Audio Files

#### Serve Audio File
- **GET** `/audio/{filename}`
- **Response**: Audio file (audio/ogg)
- **Example**: `/audio/d83d0168-34c1-4754-b983-f6c16fc0ec30.ogg`

### Health Check

#### Ping
- **GET** `/ping`
- **Response**: `{ "status": "ok", "message": "pong" }`

#### Health Check
- **GET** `/health`
- **Response**: Detailed health status including database and bot status

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message"
}
```

Common HTTP status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Authentication

To authenticate requests, include the Bearer token in the Authorization header:

```
Authorization: Bearer <access_token>
```

Example using curl:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/admin/users
```

## Pagination

All list endpoints support pagination with the following query parameters:
- `page`: Page number (starts from 1)
- `limit`: Number of items per page

Response includes:
- `data`: Array of items
- `total`: Total number of items
- `page`: Current page
- `limit`: Items per page
- `pages`: Total number of pages
