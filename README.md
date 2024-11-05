# 🎬 Media Management API

Welcome to the **Media Management API**! This FastAPI application allows you to manage media items and their associated timestamps securely. The API supports user authentication and role-based access control, enabling different functionalities for admin and regular users.

## 🚀 Features

- **User Authentication**: Secure login and token-based access.
- **CRUD Operations**: Create, Read, Update, and Delete media items.
- **Role-Based Access Control**: Admins can manage media and timestamps.
- **SQLite Database**: Simple and efficient data storage.

## 📦 Installation

To get started, clone this repository and install the required packages.

### Step 1: Clone the repository

```bash
git clone https://github.com/Ankitjarwall/TimeStamps
cd media-management-api
```

### Step 2: Create a virtual environment (optional)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Step 3: Install dependencies

```bash
pip install fastapi[all] sqlalchemy passlib python-jose
```

### Step 4: Run the application

```bash
uvicorn main:app --reload
```

## 🛠️ Usage

After running the application, you can access the API at `http://127.0.0.1:8000`.

### API Documentation

You can find the interactive API documentation at `http://127.0.0.1:8000/docs`.

## 🔑 Authentication

To use the protected endpoints, you'll need to log in to get an access token. Use the `/token` endpoint to authenticate.

### Example Login Request

```bash
POST /token
Content-Type: application/x-www-form-urlencoded

username=admin&password=adminpassword
```

### Example Token Response

```json
{
    "access_token": "your_access_token",
    "token_type": "bearer"
}
```

## 📋 API Endpoints

Here are the main endpoints available in the API:

### Media Endpoints

- **Add Media**
  - `POST /media/`
  - Requires admin role.
  
- **Get Media by ID**
  - `GET /media/{media_id}`

- **Delete Media**
  - `DELETE /media/{media_id}`
  - Requires admin role.

- **Get All Media**
  - `GET /media/?limit=10`

## 📄 Models

### Media
- `media_id`: Unique identifier for the media (string).
- `title`: Title of the media (string).
- `timestamps`: List of associated timestamps.

### Timestamp
- `type`: Type of the timestamp (string).
- `start_time`: Start time in "HH:MM:SS" format.
- `end_time`: End time in "HH:MM:SS" format.

## 📝 Notes

- **Database**: The application uses an SQLite database (`media.db`). Ensure you have write access to the directory.
- **Security**: Change the `SECRET_KEY` in the code before deploying to production.

## 🛠️ Contributing

Contributions are welcome! Please create a pull request for any enhancements or bug fixes.

## 🎉 Happy Coding!
```

### Notes
- Replace `yourusername` and `your_email@example.com` with your actual GitHub username and email.
- Adjust the API documentation and any other details according to your project specifics as needed.