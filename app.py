from flask import Flask, render_template, flash, redirect, url_for, session, request, logging # Imports Flask and renders the template
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt # Encrypts my password
from functools import wraps

app = Flask(__name__) # Placeholder for app.py

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost' # name of host to connect to
app.config['MYSQL_USER'] = 'root' # user to authenticate as Default
app.config['MYSQL_PASSWORD'] = 'password' # password to authenticate with Default
app.config['MYSQL_DB'] = 'myflaskapp' # database to use Default
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app) # initializes mysql

# Index
@app.route('/') # Route for our index page/Front page
def index(): # Defines the function index
    return render_template('home.html') # Anything you put home.html will appear

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Register form class
class RegisterForm(Form): # Defining my forms with a subclass of (Form)
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.length(min=1, max=25)])
    email = StringField('Email', [validators.length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# User register
@app.route('/register', methods=['GET', 'POST']) # GET retrieves the info while POST creates it
def register():
        form = RegisterForm(request.form)
        if request.method == 'POST' and form.validate(): # if the form is submitted do the following...
            name = form.name.data
            email = form.email.data
            username = form.username.data
            password = sha256_crypt.encrypt(str(form.password.data)) # str defimes the right side value

            # Create cursor
            cur = mysql.connection.cursor()

            # Execute query
            cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('You are now registered and can log in', 'Success!')

            return redirect(url_for('login')) # After you sign up it redirects you to the login page
        return render_template('register.html', form=form) # Passes form value into the template ('register.html') 


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone() # Looks at the query ^ and fetches only one 
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username # var (username) comes from the form

                flash('You are now logged in', 'success') # If correct password say this
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login' # If incorrect password say this
                return render_template('login.html', error=error) # if error do as i say in (_messages.html)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f): # takes in a parameter f
    @wraps(f) # pass in the f value
    def wrap(*args, **kwargs): # no idea what the value in this means
        if 'logged_in' in session: 
            return f(*args, **kwargs) # *args and **kwargs allow you to pass a variable number of arguments to a function
        else: 
            flash('Unauthorized, Please login', 'danger') # if not logged in you will get an error
            return redirect(url_for('login'))
    return wrap

# Logout 
@app.route('/logout')
def logout():
    session.clear() # kills session
    flash("You are now logged out", "success")
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__': # The script will be executed
    app.secret_key='dsperezsilva171'
    app.run(debug=True, host='0.0.0.0') # Runs the app / Debug mode means wont have to rerun to server to see changes 

