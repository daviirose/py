from flask import Flask, render_template, flash, redirect, url_for, session, request, jsonify, logging # Imports Flask and renders the template
from pusher import Pusher
import json
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from flask_mysqldb import MySQL
from passlib.hash import sha256_crypt # Encrypts my password
from functools import wraps



# creates flask app
app = Flask(__name__) # Placeholder for app.py

app.static_folder = 'static'

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

# Articles
@app.route('/articles')
def articles():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if result > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)

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
@app.route('/register', methods=['GET', 'POST']) # POST retrieves the info while GET creates it
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

                flash('You are now logged in', 'success') # If correct password say this and redirect you to DB
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
    def wrap(*args, **kwargs): 
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
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()
    
# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


    # configure pusher object
pusher = Pusher(
    app_id='661600',
    key='1bce7c3f2ef0f1951e3d',
    secret='660465b57dd5b226d9bb',
    cluster='us2',
    ssl=True
)

 # main route, shows main.html view
@app.route('/main')
def todo():
    return render_template('main.html')

# endpoint for storing todo item
@app.route('/add-todo', methods = ['POST'])
def addTodo():
    data = json.loads(request.data.decode("utf-8")) # load JSON data from request
    pusher.trigger('todo', 'item-added', data) # trigger `item-added` event on `todo` channel
    return jsonify(data)

# endpoint for deleting todo item
@app.route('/remove-todo/<item_id>')
def removeTodo(item_id):
    data = {'id': item_id }
    pusher.trigger('todo', 'item-removed', data)
    return jsonify(data)  

# endpoint for updating todo item
@app.route('/update-todo/<item_id>', methods = ['POST'])
def updateTodo(item_id):
    data = {
    'id': item_id,
    'completed': json.loads(request.data.decode("utf-8")).get('completed', 0)
    }
    pusher.trigger('todo', 'item-updated', data)
    return jsonify(data)  


if __name__ == '__main__': # The script will be executed
    app.secret_key='dsperezsilva171'
    app.run(debug=True, host='192.168.33.10') # Runs the app / Debug mode means wont have to rerun to server to see changes 


