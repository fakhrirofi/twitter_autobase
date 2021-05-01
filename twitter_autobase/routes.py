from . import app
from .forms import LoginForm, RegisterForm
from .models import User
from flask import redirect, url_for, render_template, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

@app.route("/")
@app.route("/index")
@login_required
def index():
    posts = [
        {
            'author'    : {'username': 'testing'},
            'body'      : 'Hello world'
        },
        {
            'author'    : {'username': 'testing2'},
            'body'      : 'Hello universe'
        }
    ]
    return render_template("index.html", title="Home", posts=posts)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)

    return render_template("login.html", title='Sign in', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))
