# annotator.py
# Core logic for forum data annotator application.
# 
# Author: Alex Kindel
# Date: 19 July 2016

import os

from flask import Flask, g, render_template, request, url_for, redirect, session
from werkzeug import generate_password_hash, check_password_hash
import sqlite3


# Configuration
DATABASE = "data/annotator.db"
SECRET_KEY = "DEBUG"
THREADS = "data/threads.csv"

# Create application container
app = Flask(__name__)
app.config.from_object(__name__)


## Database management

def open_db():
	if not hasattr(g, 'sqlite_db'):
		g.sqlite_db = sqlite3.connect(app.config['DATABASE'])
		g.sqlite_db.row_factory = sqlite3.Row  # treat db rows as dicts
	return g.sqlite_db

@app.cli.command('build')
def build_db():
	db = open_db()
	with open('sql/schema.sql') as f:
		db.executescript(f.read())
	db.commit()

@app.cli.command('load')
def load_db():
	db = open_db()
	with open(app.config['THREADS']) as t:
		pass  # TODO: load thread data

@app.teardown_appcontext
def close_db(error):
	if hasattr(g, 'sqlite_db'):
		g.sqlite_db.close()


## User session management

@app.before_request
def set_user():
	'''Attach user information to HTTP requests.'''
	g.user = None
	if 'user_id' in session:
		db = open_db()
		g.user = db.execute("SELECT * FROM users WHERE id = ?", [session['user_id']]).fetchone()
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	'''Log in as user.'''
	if g.user:
		return redirect(url_for('index'))
	if request.method == 'POST':
		db = open_db()
		user = db.execute("SELECT * FROM users WHERE username = ?", [request.form['username']]).fetchone()
		if not user:
			print "Invalid username."
		elif not check_password_hash(user['pass_hash'], request.form['password']):
			print "Invalid password."
		else:
			session['user_id'] = user['id']
			return redirect(url_for('index'))
	return render_template('login.html')

@app.route('/logout')
def logout():
	'''Logout active user.'''
	session.pop('user_id', None)
	return redirect(url_for('index'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
	if request.method == 'POST':
		db = open_db()
		su = (request.form.get('superuser') == 'on')
		db.execute("insert into users(username, first_name, last_name, email, pass_hash, superuser) values (?,?,?,?,?,?)",
			  [request.form['username'], request.form['first_name'], request.form['last_name'], request.form['email'], generate_password_hash(request.form['password']), su])
		db.commit()
		return redirect(url_for('users'))
	db = open_db()
	users = db.execute('select id, username, first_name, last_name, superuser from users').fetchall()
	return render_template('admin.html', users=users)


## Annotator administration

@app.route('/assign', methods=['GET', 'POST'])
def assign():
	if not g.user:
		return redirect(url_for('login'))
	if not g.user['superuser']:
		return redirect(url_for('users'))
	db = open_db()
	if request.method == 'POST':
		pass  # TODO: Assign threads to users by checking boxes in a table
	else:
		users = db.execute("SELECT * FROM users ORDER BY id").fetchall()
		return render_template('assignments.html', users=users)


## Main page

@app.route('/')
def index():
	return render_template('index.html')


if __name__ == "__main__":
    app.run()