
from flask import Flask, make_response, request, g, abort
import os
from datetime import datetime
from flask_login import UserMixin 
from flask_migrate import Migrate
from flask_httpauth import HTTPBasicAuth,HTTPTokenAuth
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth()

class config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONs')


app = Flask(__name__)
app.config.from_object(config)
db =SQLAlchemy(app)
migrate = Migrate(app, db)
basic_auth = HTTPBasicAuth(app)

@token_auth.verify_token
def verify_token(token):
    u = User.check_token(token) if token else None
    g.current_user = u
    return u

@basic_auth.verify_password
def verify_password(email, password):
    u= User.Query.filter_by(email=email).first()
    if u is None:
        return False
    g.current_user =u
    return u.check_hashed_password(password)


class User(UserMixin, db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    fame = db.Column(db.String)
    lame = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    # book = db.relationship('Book', backref="cat", 
    #             lazy="dynamic", cascade="all, delete-orphan")
    
    def hash_password(self, original_password):
        return generate_password_hash(original_password)
    
    def check_hashed_password(self, login_password):
        return check_password_hash(self.password, login_password)


    def __repr__(self):
        return f'<Category: {self.id}|{self.name}>'

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        return {
            "user_id":self.user_id,
            "fname":self.fname,
            "lname":self.lname,
            "email":self.email
        }  


    def from_dict(self, data):
        self.fname = data['fname']
        self.lname = data['lname']
        self.email=data['email']
        self.password = self.hash_password(data['password'])



class Book(db.Model):
    book_id=db.Column(db.Integer, primary_key=True)
    tittle=db.Column(db.String)
    author = db.Column(db.String)
    pages = db.Column(db.Integer)
    summary = db.Column(db.Text)
    image = db.Column(db.String)
    subject = db.Column(db.String)
    created_on=db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # user_id=db.Column(db.ForeignKey('user.user_id'))
    
    def __repr__(self):
        return f'<Item: {self.id}|{self.name}>'

    def save(self):
        db.session.add(self)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        return {
            'user_id':self.user_id,
            'tittle':self.tittle,
            'author':self.author,
            'pages':self.pages,
            'summary':self.summary,
            'subject':self.subject,
            'created_on':self.created_on,
            'book_id':self.book_id,
        }

    def from_dict(self, data):
        for field in ['tittle','author','pages','summary','subject', 'created_on','book_id']:
            if field in data:
                    #the object, the attribute, value
                setattr(self, field, data[field])

@app.get('/token')
@basic_auth.login_required()
def get_token():
    token = g.current_user.get_token()
    return make_response({"token":token}, 200)


@app.get('/login')
@basic_auth.login_required()
def get_login():
    user = g.current_user
    token  = user.get_token()
    return make_response({"token":token, **user.to_dict()},200)


@app.get('/post')
@token_auth.login_required()
def get_user():
    return make_response({"users":[user.to_dict() for user in User.query.all()]},200)

@app.get('/post/<int:user_id>')
def get_user_by_id(user_id):
    return make_response(User.query.get(user_id).to_dict(),200)


@app.post('/user')
# @token_auth.login_required()
def post_user():
    data=request.get_json()
    new_user=User()
    new_user.from_dict(data)
    new_user.save()
    return make_response("success", 200)

@app.put('/user/<int:user_id>')
@token_auth.login_required()
def put_user(user_id):
    data=request.get_json()
    user=User.query.get(user_id)
    user.from_dict(data)
    user.save()
    return make_response("success", 200)

@app.delete('/delete/<int:user_id>')
@token_auth.login_required()
def delete_category(user_id):
    cat = User.query.get(user_id)
    if not cat:
        abort(404)
    cat.delete()
    return make_response(f"User {user_id} has been deleted", 200)




@app.get('/book')
def get_books():
    # Get all the items in the db
    books = Book.query.all()
    # Turn items to dictionary
    book_dicts= [book.to_dict() for book in books]
    # return the response
    return make_response({"books":book_dicts}, 200)   

@app.get('/book/<int:book_id>')
def get_item(book_id):
    # Look up the item in the database
    book = Book.query.get(book_id)
    # Verify it exists
    if not book:
        abort(404)
    # Turn item into Dictionary
    book_dict = book.to_dict()
    # return Response
    return make_response(book_dict,200) 
    

# # Get all items in a Category (by cat id)
# @app.get('/book/category/<int:book_id>')
# def get_book_by_cat(book_id):
#     cat = Book.query.get(book_id)
#     if not cat:
#         abort(404)
#     all_book_in_cat = [book.to_dict() for book in cat.products]
#     return make_response({"book":all_book_in_cat}, 200)


@app.post('/books')
def post_book():
    # Get the Payload from the request
    book_dict = request.get_json()
    # Ensure the payload has all the approiate values
    if not all(key in book_dict for key in ('tittle','author','pages','summary','subject', 'created_on', 'book_id')):
        abort(400)
    # Create an empty Item
    book = Book()
    # bookthe attributes of that item to the payload
    book.from_dict(book_dict)
    # book Item
    book.save()
    # Send response
    return make_response(f"Book {book.tittle} was created with an id {book.book_id}",200)


# some sort of dict {}
@app.put("/book/<int:book_id>")
def put_item(book_id):
    book_dict = request.get_json()
    book = Book.query.get(id)
    if not book:
        abort(404)
    book.from_dict(book_dict)
    book.save()
    return make_response(f"Book {book.tittle} with ID {book.book_id} has been updated", 200)


# Delete a Item by ID
@app.delete('/book/<int:book_id>')
def delete_item(book_id):
    book_to_delete = Book.query.get(id)
    if not book_to_delete:
        abort(404)
    book_to_delete.delete()
    return make_response(f"Item with id: {book_id} has been delted", 200)


@app.get('/book/users/<int:user_id>')
def get_book_by_user_id(user_id):
    return make_response({"books":[book.to_dict() for book in User.query.all(user_id).books]},200)

# good one to learn 