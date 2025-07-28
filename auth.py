from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from .models import Usuario
from . import db, login_manager

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Credenciales incorrectas')
    return render_template('login.html')

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))