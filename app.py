from flask import Flask # Imports Flask


app = Flask(__name__) # Placeholder for app.py

@app.route('/') # Route for our index page/Front page
def index(): # Defines the function index
    return 'INDEX5' # What pops up on the UI


if __name__ == '__main__': # The script will be executed
    app.run(debug=True) # Runs the app / Debug mode means wont have to rerun to server to see changes
