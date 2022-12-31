from flask import Blueprint, render_template, request, flash, redirect, url_for
from werkzeug.security import check_password_hash
from .models import User
from flask_login import login_user, login_required, logout_user, current_user
from .dal import add_user

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                return redirect(url_for('view.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successfully!', category='success')
    return redirect(url_for('auth.login'))


@auth.route('/create-user', methods=['GET', 'POST'])
@login_required
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        import re

        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.fullmatch(regex, email):
            flash('Emtpy email address.', category='error')
        elif password1 != password2:
            flash('Password does not match!.', category='error')
        elif len(password1) < 4:
            flash('Password must be of minimum length 4')
        else:
            if not add_user(email, password1):
                flash('Email already exists', category='error')
    return render_template('signup.html')
