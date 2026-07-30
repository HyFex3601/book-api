from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from app.database import Base, engine, SessionLocal
from app import models
from sqlalchemy.orm import Session
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
import json
from app.cache import redis_engine
from fastapi import Request

Base.metadata.create_all(bind=engine)

app = FastAPI()




class Book(BaseModel):

    title: str
    author: str

class UserCreate(BaseModel):
    username: str
    password: str



        
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


books = [
    {
        "id": 1,
        "title": "The Hobbit",
        "author": "J.R.R Tolkien"
    },
    {
        "id": 2,
        "title": "1984",
        "author": "George Orwell"
    },
    {
        "id": 3,
        "title": "Dune",
        "author": "Frank Herbert"
    }
]


@app.post("/books")
def book_add(book: Book, db: Session = Depends(get_db), cu: str = Depends(get_current_user)):

    new_book = models.Book(title=book.title, author=book.author)

    db.add(new_book)
    db.commit()
    redis_engine.delete("all_books")
    db.refresh(new_book)
    return new_book

@app.get("/books")
def get_books(db: Session = Depends(get_db)):
    cached_books = redis_engine.get("all_books")

    if cached_books is not None:
        convert_cache = json.loads(cached_books)
        return convert_cache
    else:
        db_books =  db.query(models.Book).all()
        json_book = [{"id": book.id, "title": book.title, "author": book.author} for book in db_books]
        all_books = json.dumps(json_book)
        print("CACHE DELETED")
        redis_engine.set("all_books", all_books)
        return json_book




@app.get("/books/{book_id}")
def get_book(book_id: int, db:Session = Depends(get_db)):
    
    filter_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    
    if filter_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return filter_book


@app.get("/authors")
def get_authors(db: Session = Depends(get_db)):
    
    all_authors = db.query(models.Book.author).all()

    real_authors = []
    for authors in all_authors:
        real_authors.append(authors[0])

    return real_authors

@app.get("/search")
def search(author: str, db: Session = Depends(get_db)):

    results = db.query(models.Book).filter(models.Book.author == author).all()

    if results:
        return results
    else:
        raise HTTPException(status_code=404, detail="Author not Found")
    


@app.delete("/delete/{book_id}")
def delete_book(book_id: int,cu: str = Depends(get_current_user), db: Session = Depends(get_db)):
            
    deleted_book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if deleted_book is not None:
        db.delete(deleted_book)
        db.commit()
        return {"message": "Book Deleted Successfully"}
    else:
        raise HTTPException(status_code=404, detail="Book not found")


@app.put("/books/{book_id}")
def update_book(book_id: int, book: Book, db : Session = Depends(get_db), cu: str = Depends(get_current_user)):
    
        book_update = db.query(models.Book).filter(models.Book.id == book_id).first()

        if book_update is not None:
            book_update.author = book.author 
            book_update.title = book.title 
        
            db.commit()
            db.refresh(book_update)
            return "Book Updated Successfully"
        else:
            raise HTTPException(status_code=404, detail="Book not found")


@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    check_user = db.query(models.User).filter(models.User.username == user.username).first()

            
    if check_user is not None:
        raise HTTPException(status_code=400, detail="Username already taken")
    else:
        new_user = models.User(username = user.username, hashed_password = hash_password(user.password))
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {"message" : "User added Successfully"}
    
@app.post("/login")
def login(info: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db), request: Request = ...):

    client_ip = request.client.host
    rate_limit_key = f"login_attempts:{client_ip}"

    login_attempts = redis_engine.get(rate_limit_key)

    if login_attempts is None:
        login_attempts = 0

    if int(login_attempts) >= 5:
        raise HTTPException(status_code=429, detail="Too many requests")

    redis_engine.incr(rate_limit_key)

    if login_attempts == 0:
        redis_engine.expire(rate_limit_key, 60)


    check_username = db.query(models.User).filter(models.User.username == info.username).first()

    if check_username is not None:
        exist_user = verify_password(info.password, check_username.hashed_password)
        if exist_user:
            token = create_access_token({"sub": info.username})
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException (status_code=401, detail="Incorrect Password")
    else: 
        raise HTTPException (status_code=404, detail="User not Found")
