import math
from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
# from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import socket
socket.getaddrinfo('127.0.0.1', 8080)

# LOAD JSON
with open('config.json', 'r') as f:
    params = json.load(f)['params']
localserver = True
app = Flask(__name__)
# set the secret session key
app.secret_key = 'mongo-node-express'
app.config['UPLOAD_FOLDER'] = params['upload_location']
# app.config.update(
#     DEBUG=True,
#     MAIL_SERVER = "smtp.gmail.com",
#     MAIL_PORT = '465',
#     MAIL_USE_SSL = True,
#     MAIL_USERNAME=params['gmail_user'],
#     MAIL_PASSWORD = params['gmail_password'],
# )
# mail = Mail(app)
if (localserver):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']
db = SQLAlchemy(app)  # initialization

# class that define database tables
# CONTACT DATABASE


class Contact(db.Model):
    # sno , name, email , phone_num ,mes, date
    sno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_num = db.Column(db.Integer, nullable=True)
    mes = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String, nullable=True)

# POST TABLE


class Post(db.Model):
    sno = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(60), nullable=False)
    slug = db.Column(db.String(25), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String, nullable=True)
    img_file = db.Column(db.String(12), nullable=True)

# HOME PAGE


@app.route('/')
def home():
    posts = Post.query.filter_by().all()
    last = int(math.ceil(len(posts)) /
               int(params['no_of_post']))  # TOTAL PAGES
    print(last)
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1) * int(params['no_of_post']): (page-1)
                  * int(params['no_of_post']) + int(params['no_of_post'])]
    if(page == 1):  # MAIN PAGE
        prev = '#'
        next = "/?page=" + str(page+1)
    elif (page >= last):  # END OF POSTS
        print('running')
        prev = "/?page=" + str(page - 1)
        next = '#'
    else:  # MID OF POST PAGES
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)
    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

# ABOUT PAGE


@app.route('/about')
def about():
    return render_template('about.html', params=params)

# CONTACT PAGE


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if (request.method == 'POST'):
        # ADD ENTRY TO DATABASE
        name = request.form.get('name')
        email = request.form.get('email')
        phone_num = request.form.get('phone_num')
        mes = request.form.get('message')
        entry = Contact(name=name, email=email,
                        phone_num=phone_num, mes=mes, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html', params=params)

# POST DISPLAY


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    posts = Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params, posts=posts)

# ADMIN DASHBOARD


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    # If admin already loged in
    if ('user' in session and session['user'] == params['admin_user']):
        posts = Post.query.all()
        return render_template('dashboard.html', params=params, posts=posts)
    # get credentials
    elif request.method == 'POST':
        username = request.form.get('uname')
        password = request.form.get('password')
        # check credentials
        if username == params['admin_user'] and password == params['admin_password']:
            # set the session
            session['user'] = username
            post = Post.query.all()
            return render_template('dashboard.html', params=params, post=post)

    return render_template('signin.html', params=params, )

# EDIT OR ADD POST


@app.route('/edit/<string:post_sno>', methods=['GET', 'POST'])
def edit(post_sno):
    # If admin already loged in
    if ('user' in session and session['user'] == params['admin_user']):

        if request.method == 'POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            content = request.form.get('content')

            if post_sno == "0":
                post = Post(title=title, slug=slug, content=content,
                            img_file=img_file, date=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                post = Post.query.filter_by(sno=post_sno).first()
                post.title = title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = datetime.now()
                db.session.commit()
                return redirect('/edit/'+post_sno)
    post = Post.query.filter_by(sno=post_sno).first()
    return render_template('edit.html', params=params, post=post, post_sno=post_sno)


# FILE UPLOADER
@app.route('/uploader', methods=['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            f = request.files['file1']
            f.save(os.path.join(
                app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
    return "Uploaded Successfully"

# LOGOUT


@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/dashboard')

# DELETE POST


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Post.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')


app.run(debug=True)
