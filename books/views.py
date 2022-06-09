from flask import Blueprint, request, jsonify
import requests
import json
from .models import Book
from . import db


views = Blueprint("views", __name__)


api_spec = {
    "info" : {"version" : "2022.05.16"}
}


@views.route("/")
def index():
    return "ok"


@views.route("/books")
def books():
    parameters = request.args
    if parameters:
        external_id = parameters.get('external_id', "")
        author = parameters.get('author', "")
        title = parameters.get('title', "")
        fromDate = parameters.get('from', 0)
        toDate = parameters.get('to', 3000)
        acquired = parameters.get('acquired', "")

        if acquired:
            books = Book.query.filter(Book.published_year >= fromDate, 
                                    Book.published_year <= toDate, 
                                    Book.authors.contains(author), 
                                    Book.title.contains(title),
                                    Book.external_id.contains(external_id), 
                                    Book.acquired == (acquired.lower() == 'true')).all()
        else:
            books = Book.query.filter(Book.published_year >= fromDate, 
                                    Book.published_year <= toDate, 
                                    Book.authors.contains(author), 
                                    Book.title.contains(title)).all()

        booksList = []
        for book in books:
            book_object = {}
            book_object['id'] = book.id
            book_object['external_id'] = book.external_id
            book_object['title'] = book.title
            book_object['authors'] = json.loads(book.authors)
            book_object['published_year'] = book.published_year
            book_object['acquired'] = book.acquired
            book_object['thumbnail'] = book.thumbnail
            booksList.append(book_object)
        
        return jsonify(booksList)
    else:
        books = Book.query.all()
        booksList = []
        for book in books:
            book_object = {}
            book_object['id'] = book.id
            book_object['external_id'] = book.external_id
            book_object['title'] = book.title
            book_object['authors'] = json.loads(book.authors)
            book_object['published_year'] = book.published_year
            book_object['acquired'] = book.acquired
            book_object['thumbnail'] = book.thumbnail
            booksList.append(book_object)
        return jsonify(booksList)


@views.route("/books/<id>")
def book(id):
    book = Book.query.filter_by(id=id).first()
    if not book:
        return 'Record does not exist'
    book_object = {}
    book_object['id'] = book.id
    book_object['external_id'] = book.external_id
    book_object['title'] = book.title
    book_object['authors'] = json.loads(book.authors)
    book_object['published_year'] = book.published_year
    book_object['acquired'] = bool(book.acquired)
    book_object['thumbnail'] = book.thumbnail
    return book_object


@views.route("/api_spec")
def spec():
    return api_spec


@views.route("/books", methods=['POST'])
def add_book():
    body_data = request.json
    if 'external_id' in body_data.keys():
        external_id = body_data['external_id']
    else:
        external_id = None
    if 'title' in body_data.keys():
        title = body_data['title']
    else:
        title = None
    if 'authors' in body_data.keys():
        authors = json.dumps(body_data['authors'])
    else:
        authors = None
    if 'published_year' in body_data.keys():
        published_year = body_data['published_year']
    else:
        published_year = None
    if 'acquired' in body_data.keys():
        acquired = body_data['acquired']
    else:
        acquired = None
    if 'thumbnail' in body_data.keys():
        thumbnail = body_data['thumbnail']
    else:
        thumbnail = None

    new_book = Book(external_id = external_id, 
                    title = title, 
                    authors = authors, 
                    published_year = published_year, 
                    acquired = acquired, 
                    thumbnail = thumbnail)
    db.session.add(new_book)
    db.session.commit()
    return jsonify({"id": new_book.id,
                    "external_id": new_book.external_id,
                    "title" : new_book.title,
                    "authors": json.loads(new_book.authors),
                    "published_year": new_book.published_year,
                    "acquired": new_book.acquired,
                    "thumbnail": new_book.thumbnail
    })


@views.route("/books/<id>", methods=['PATCH'])
def update_book(id):
    body_data = request.json
    book = Book.query.filter_by(id=id).first()
    if not book:
        return "Record does not exist"
    
    if 'external_id' in body_data.keys():
        book.external_id = body_data['external_id']
    if 'title' in body_data.keys():
        book.title = body_data['title']
    if 'authors' in body_data.keys():
        book.authors = body_data['authors']
    if 'published_year' in body_data.keys():
        book.published_year = body_data['published_year']
    if 'acquired' in body_data.keys():
        book.acquired = body_data['acquired']
    if 'thumbnail' in body_data.keys():
        book.thumbnail = body_data['thumbnail']
    
    db.session.commit()
    return jsonify({"id": book.id,
                    "external_id": book.external_id,
                    "title" : book.title,
                    "authors": json.loads(book.authors),
                    "published_year": book.published_year,
                    "acquired": book.acquired,
                    "thumbnail": book.thumbnail
    })


@views.route("/import", methods=['POST'])
def import_books():
    body_data = request.json
    author = body_data['author']
    startIndex = 0
    maxResult = 40
    book_objects = requests.get(f'https://www.googleapis.com/books/v1/volumes?q=inauthor:{author}&startIndex={startIndex}&maxResults={maxResult}').json()

    for book_object in range(len(book_objects['items'])):
        if "id" in book_objects['items'][book_object]:
            ext_id = book_objects['items'][book_object]["id"]
        else:
            ext_id = None

        if "title" in book_objects['items'][book_object]['volumeInfo']:
            title = book_objects['items'][book_object]['volumeInfo']['title']
        else:
            title = None

        if "authors" in book_objects['items'][book_object]['volumeInfo']:
            authors = json.dumps(book_objects['items'][book_object]['volumeInfo']["authors"])
        else:
            authors = None

        if "publishedDate" in book_objects['items'][book_object]['volumeInfo']:
            publishedYear = book_objects['items'][book_object]['volumeInfo']["publishedDate"][:4]
        else:
            publishedYear = None

        if "imageLinks" in book_objects['items'][book_object]['volumeInfo']:
            thumbnail = book_objects['items'][book_object]['volumeInfo']['imageLinks']['thumbnail']
        else:
            thumbnail = None

        imported_book = Book(external_id = ext_id, 
                            title = title, 
                            authors = authors, 
                            published_year = publishedYear, 
                            thumbnail = thumbnail)
        db.session.add(imported_book)
        db.session.commit()
    imported = {"imported": len(book_objects['items'])}
    return imported


@views.route("/books/<id>", methods=['DELETE'])
def delete(id):
    book = Book.query.filter_by(id=id).first()
    db.session.delete(book)
    db.session.commit()
    return jsonify(f"Book with id {id} deleted")