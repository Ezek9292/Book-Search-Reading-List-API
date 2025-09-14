from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from database import reading_list_collection
import requests
from dotenv import load_dotenv

load_dotenv()


# Titble of project
app = FastAPI(
    title="📚 Ezekiel Library API",
    description="Search books with Google Books API"
)

# Module
class Book(BaseModel):
    title: str
    authors: List[str]
    published_date: Optional[str] = None
    user_status: Optional[str] = None 


# this funtion works like "replace_mongo_id" 
def database_converts(book) -> dict:
    """Convert MongoDB object to dict with string id"""
    return {
        "id": str(book["_id"]),
        "title": book["title"],
        "authors": book["authors"],
        "published_date": book.get("published_date"),
        "user_status": book.get("user_status"),
    }



# 1. Search books from Google API
@app.get("/books/{title}", tags=["Books"])
def search_books(title: str, max_results: int = 5):
    url = f"https://www.googleapis.com/books/v1/volumes?q={title}&maxResults={max_results}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Invalid request")
    
    data = response.json()
    books = []
    
    for item in data.get("items", []):
        volume = item["volumeInfo"]
        books.append({
            "title": volume.get("title"),
            "authors": volume.get("authors", []),
            "published_date": volume.get("publishedDate", "Unknown")
        })
    
    return {"results": books}

# 2. Save Book to Reading List
@app.post("/reading_list", tags=["Reading List"])
def add_to_reading_list(book: Book):
    book_dict = book.model_dump()
    result = reading_list_collection.insert_one(book_dict)
    book_dict["_id"] = str(result.inserted_id)
    return {"message": "Book added to reading list successfully✅"}

# 3. Get All Reading List
@app.get("/reading_list", tags=["Reading List"])
def get_reading_list():
    books = reading_list_collection.find()
    return {"reading_list": [database_converts(book) for book in books]}

# 4. Get Recommendations by Same Author
@app.get("/recommendations/{author}", tags=["Recommendations"])
def get_recommendations(author: str, max_results: int = 5):
    url = f"https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&maxResults={max_results}"
    response = requests.get(url)
    
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Google Books API error")
    
    data = response.json()
    recs = []
    
    for item in data.get("items", []):
        volume = item["volumeInfo"]
        recs.append({
            "title": volume.get("title"),
            "authors": volume.get("authors", []),
            "published_date": volume.get("publishedDate", "Unknown")
        })
    
    return {"recommendations": recs}