from flask import Flask, render_template, request, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, TextAreaField, StringField, PasswordField, validators
from data import Products
from functools import wraps
from passlib.hash import sha256_crypt

app = Flask(__name__)

#database config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mz623mz623'
app.config['MYSQL_DB'] = 'website'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)
Products = Products()

#index page
@app.route("/")
@app.route("/<user>")
def index(user = None):
	return render_template('home.html', user = user)

#product page
@app.route("/products")
def products():
	return render_template('products.html', products = Products)

#register form data 
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=6, max=20)])
	email = StringField('Email', [validators.Length(min=6, max=30)])
	password = PasswordField('Password', [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords do not match')])
	confirm = PasswordField('Confirm Password')

#register page
@app.route("/register", methods = ['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		#store data
		name = form.name.data
		email = form.email.data
		username = form.username.data
		#encrypt
		password = sha256_crypt.encrypt(str(form.password.data))

		#cursor
		cur = mysql.connection.cursor()

		#execute sql statement
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		#commit to database
		mysql.connection.commit()

		#close database connection and success meessages popped
		cur.close()
		flash('Registered Successfully', 'success')

		#redirect to index page
		return redirect(url_for('index'))

	return render_template('register.html', form = form)

#login page
@app.route('/login', methods = ['GET', 'POST'])
def login():
	if request.method == 'POST':
		#get data
		username = request.form['username']
		passwordc = request.form['password']

		#cursor
		cur = mysql.connection.cursor()

		#execute sql statement
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			#check username and password
			data = cur.fetchone()
			password = data['password']

			if sha256_crypt.verify(passwordc, password):
				#login successfully process
				session['logged_in'] = True
				session['username'] = username
				flash('Logged In', 'success')
				return redirect(url_for('orders'))

			else:
				#wrong password process
				error = ('Wrong Password')
				return render_template('login.html', error = error)
			cur.close()

		else:
			#wrong username process
			error = ('Username Not Found')
			return render_template('login.html', error = error)

	return render_template('login.html')

#function to stop user access to dashboard/order before logging in
def is_logged_in(x):
	@wraps(x)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return x(*args, **kwargs)

		else:
			#flash message and redirect to login page
			flash('Please Login', 'danger')
			return redirect(url_for('login'))

	return wrap

#dashboard page
@app.route("/dashboard")
#determine logged in or ont
@is_logged_in
def dashboard():

	#cursor
	cur = mysql.connection.cursor()

	#execute sql statement
	#get data form table products
	result = cur.execute("SELECT * FROM products")
	products = cur.fetchall()

	if result > 0:
		#display data from database
		return render_template('dashboard.html', products = products)

	else:
		#if no data
		msg = ('No products Found')
		return render_template('dashboard.html')

	#close database connection
	cur.close()

#form for users to post
class ProductForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=10)])

#add products function
@app.route('/add_product', methods=['GET', 'POST'])
#determine logged in or not
@is_logged_in
def add_product():
	#create form
    form = ProductForm(request.form)
    if request.method == 'POST' and form.validate():

    	#get data from input
        title = form.title.data
        body = form.body.data

        #cursor
        cur = mysql.connection.cursor()

        #execute sql statement
        cur.execute("INSERT INTO products(title, body, created_by) VALUES(%s, %s, %s)",(title, body, session['username']))

        #commit to databse
        mysql.connection.commit()

		#close database connection
		#flash meesage for created successfully and redirect to dashboard page
        cur.close()
        flash('Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_product.html', form = form)

#orders page
@app.route("/orders")
def orders():

	#cursor
	cur = mysql.connection.cursor()

	#execute sql statement
	result = cur.execute("SELECT * FROM products")
	products = cur.fetchall()

	if result > 0:
		#display data from database
		return render_template('orders.html', products = products)

	else:
		#if no data
		msg = ('No Products Found')
		return render_template('orders.html')

	#close database connection
	cur.close()

#logout
@app.route("/logout")
#determine logged in or not
@is_logged_in
def logout():

	#clear login and flash messages for logged out
	session.clear()
	flash('Logged Out', 'success')

	#redirect to login page
	return redirect(url_for('login'))

if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug = True, port = 8000)