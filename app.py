from flask import Flask, render_template # Imports Flask and renders the template


app = Flask(__name__) # Placeholder for app.py

@app.route('/') # Route for our index page/Front page
def index(): # Defines the function index
    return render_template('home.html') # Anything you put home.html will appear


if __name__ == '__main__': # The script will be executed
    app.run(debug=True) # Runs the app / Debug mode means wont have to rerun to server to see changes
