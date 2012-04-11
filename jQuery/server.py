from flask import Flask
from flask import render_template, abort, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("slapos.html")

@app.route('/200', methods=["POST", "GET"]) 
def request200():
    response = make_response("HELLO", 200)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response

@app.route('/request', methods=["POST", "GET"]) 
def request404():
    response = make_response("Not Found", 404)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response

if __name__ == '__main__':
    app.run(debug=True)