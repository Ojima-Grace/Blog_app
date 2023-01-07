from crypt import methods
from datetime import datetime
from email.policy import default
from enum import unique
from multiprocessing import context
from nis import cat
from tkinter import ttk
from turtle import pos
from unicodedata import category
from flask import Flask, render_template, url_for, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user, login_user, LoginManager, UserMixin, logout_user, login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from sqlalchemy.sql import func
import tkinter as tk
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(base_dir, 'blogging.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = '7263bdd5124a04da76f0e499a9ace817c470f9e0'

db = SQLAlchemy(app)
login_manager = LoginManager(app)

class User(db.Model, UserMixin):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    posts = db.relationship("Post", backref="user", passive_deletes=True)
    comments = db.relationship("Comment", backref="user", passive_deletes=True)
    likes = db.relationship("Like", backref="user", passive_deletes=True)


    def __repr__(self):
        return f"User <{self.username}>"

class Post(db.Model):
    __tablename__="post"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50), nullable=False)
    text = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    comments = db.relationship("Comment", backref="post", passive_deletes=True)
    likes = db.relationship("Like", backref="post", passive_deletes=True)



    def __init__(self, title, text, author):
        self.title = title
        self.text = text
        self.author = author
    
    def __repr__(self):
        return f"Post <{self.title}>"

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(140), nullable=False)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f"Comment <{self.text}>"

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime(timezone=True), default=func.now())
    author = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False)



@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))

@app.route('/')
@app.route('/home')
def index():
    posts = Post.query.all()
    posts = Post.query.order_by(Post.id.desc()).all()

    return render_template('index.html', user=current_user, posts=posts) 

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        user = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()
        password_hash = generate_password_hash(password)

        if user:
            flash('Username already exists.', category='error')
        
        elif len(username) < 2:
            flash('Username is too short', category='error')

        elif email_exists:
            flash('Email already exists.', category='error')
            
        elif len(password) < 8:
            flash('Password too short', category='error')

        elif password != password2:
            flash('Passwords don\'t match', category='error')

            return redirect(url_for('register'))

        else:
            new_user = User(username=username, firstname=firstname, lastname=lastname, email=email, password_hash=password_hash)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash("Account created successfully!", category="success")
            return redirect(url_for('login'))

    return render_template('signup.html', user=current_user)

@app.route('/create_post', methods=["GET", "POST"])
@login_required
def create_post():
    if request.method == "POST":
        title = request.form.get('title')
        text = request.form.get('text')

        post = Post(title=title, text=text, author=current_user.id)

        db.session.add(post)
        db.session.commit()
        flash("Post created successfully!", category="success")
        return redirect(url_for('index'))

    return render_template('create_post.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash("You are logged in!", category="success")
            return redirect(url_for('index'))

        else:
            flash('Email or Password is incorrect', category='error')
            return redirect(url_for('login'))
            
    return render_template('login.html', user=current_user)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
@login_required 
def contact():
    return render_template('contact.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You are now logged out!", category="success")
    return redirect(url_for('index'))

@app.route('/delete_post/<id>', methods=["GET"])
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category="error")

    else:
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully!", category="success")

    return redirect(url_for('index'))

@app.route('/edit_post/<id>', methods=["GET", "POST"])
@login_required
def edit_post(id):
    post = Post.query.filter_by(id=id).first()

    if request.method == "POST":
        title = request.form.get('title')
        text = request.form.get('text')

        post.title=title
        post.text=text

        db.session.commit()
        flash("Post edited successfully", category="success")

        return redirect(url_for("index"))
    
    return render_template("edit_post.html", post=post)

@app.route('/comment/<post_id>', methods=["GET", "POST"])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    posts = Post.query.order_by(Post.id.desc()).all()

    if request.method == "POST":
        text = request.form.get('text')
        if not text:
            flash("Comment cannot be empty!", category="error")
        else:
            flash("Comment Posted!", category="success")
            comment = Comment(text=text, author=current_user.id, post_id=post.id)

        db.session.add(comment)
        db.session.commit()

    return render_template('comment.html', post=post, posts=posts, user=current_user)

@app.route('/delete_comment/<id>', methods=["GET", "POST"])
@login_required
def delete_comment(id):
    comment = Comment.query.filter_by(id=id).first()

    if not comment:
        flash("Comment does not exist!", category="error")
    else:
        db.session.delete(comment)
        db.session.commit()
        flash("Comment deleted!", category="success")
        
    return redirect(url_for('index'))

@app.route('/like-post/<post_id>', methods=["GET", "POST"])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id)
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()
    
    if not post:
        flash("Post does not exist!", category="error")
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return redirect(url_for('index'))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.errorhandler(401)
def page_not_found(e):
    return render_template('401.html'), 401



if __name__=='__main__':
    app.run(debug=True)