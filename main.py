from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, String, Time, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import time, timedelta
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta

# Setup Database
DATABASE_URL = "sqlite:///./media.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# SQLAlchemy Models


class Media(Base):
    __tablename__ = "media"
    id = Column(Integer, primary_key=True, index=True)
    media_id = Column(String, unique=True, index=True)
    title = Column(String, index=True)
    timestamps = relationship("Timestamp", back_populates="media")


class Timestamp(Base):
    __tablename__ = "timestamps"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)
    media_id = Column(Integer, ForeignKey("media.id"))
    media = relationship("Media", back_populates="timestamps")


# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models


class TimestampBase(BaseModel):
    type: str
    start_time: Optional[str]  # Keep as str for input
    end_time: Optional[str]  # Keep as str for input


class MediaBase(BaseModel):
    media_id: str
    title: str
    timestamps: List[TimestampBase]


# User authentication setup
SECRET_KEY = "your_secret_key"  # Change this in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dummy data for users (in a real application, use a database)
users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("adminpassword"),
        "role": "admin"  # Set the role
    },
    "user": {
        "username": "user",
        "hashed_password": pwd_context.hash("userpassword"),
        "role": "user"  # Set a different role
    }
}

# Dependency to get DB session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper function to convert "HH:MM:SS" to time objects


def convert_to_time(time_str: str) -> time:
    """Convert a string in 'HH:MM:SS' format to a Python time object."""
    if time_str:
        hours, minutes, seconds = map(int, time_str.split(':'))
        return time(hour=hours, minute=minutes, second=seconds)
    return None

# User authentication functions


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return user_dict


async def authenticate_user(username: str, password: str):
    user = get_user(users_db, username)
    if not user or not verify_password(password, user["hashed_password"]):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Default expiration time
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# API Endpoints


@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=400, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/media/", response_model=MediaBase)
def add_media(media: MediaBase, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Decode the token to get the user role
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role: str = payload.get("role")
        if user_role != "admin":  # Check if the user has admin privileges
            raise HTTPException(
                status_code=403, detail="Not enough permissions")
    except JWTError:
        raise credentials_exception

    # Create new Media entry
    db_media = Media(media_id=media.media_id, title=media.title)
    db.add(db_media)
    db.commit()
    db.refresh(db_media)

    # Add timestamps for the media item
    for ts in media.timestamps:
        start_time = convert_to_time(ts.start_time)
        end_time = convert_to_time(ts.end_time)

        db_timestamp = Timestamp(
            type=ts.type,
            start_time=start_time,
            end_time=end_time,
            media_id=db_media.id
        )
        db.add(db_timestamp)
    db.commit()

    # Refresh and return the full media entry
    db.refresh(db_media)
    return media


@app.get("/media/{media_id}", response_model=MediaBase)
def get_media_timestamps(media_id: str, db: Session = Depends(get_db)):
    """
    Get timestamps for a specific media item by its media_id.
    """
    media_item = db.query(Media).filter(Media.media_id == media_id).first()
    if not media_item:
        raise HTTPException(status_code=404, detail="Media item not found")

    # Convert to Pydantic model
    return MediaBase(
        media_id=media_item.media_id,
        title=media_item.title,
        timestamps=[
            TimestampBase(type=ts.type, start_time=str(
                ts.start_time), end_time=str(ts.end_time))
            for ts in media_item.timestamps
        ]
    )


@app.delete("/media/{media_id}", response_model=dict)
def delete_media(media_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Delete a media item by its media_id.
    """
    # Decode the token to get the user role
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_role: str = payload.get("role")
        if user_role != "admin":  # Check if the user has admin privileges
            raise HTTPException(
                status_code=403, detail="Not enough permissions")
    except JWTError:
        raise credentials_exception

    media_item = db.query(Media).filter(Media.media_id == media_id).first()
    if not media_item:
        raise HTTPException(status_code=404, detail="Media item not found")

    # Delete timestamps associated with this media item
    db.query(Timestamp).filter(Timestamp.media_id == media_item.id).delete()

    # Delete the media item
    db.delete(media_item)
    db.commit()

    return {"detail": f"Media item with media_id '{media_id}' has been deleted."}


@app.get("/media/", response_model=List[MediaBase])
def get_all_media(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get up to 10 media items from the database.
    """
    media_items = db.query(Media).limit(limit).all(
    )  # This should limit results to the specified limit
    return [
        MediaBase(
            media_id=media_item.media_id,
            title=media_item.title,
            timestamps=[
                TimestampBase(type=ts.type, start_time=str(
                    ts.start_time), end_time=str(ts.end_time))
                for ts in media_item.timestamps
            ]
        ) for media_item in media_items
    ]
# To run the server, use `uvicorn main:app --reload` in the terminal
