from . import db


class Book(db.Model):
    __tablename__ = 'Book'
    id = db.Column(db.Integer, primary_key = True)
    external_id = db.Column(db.String(120), nullable = True)
    title = db.Column(db.String(120))
    authors = db.Column(db.String(200))
    published_year = db.Column(db.String(20))
    acquired = db.Column(db.Boolean, default=False)
    thumbnail = db.Column(db.String(500), nullable = True)