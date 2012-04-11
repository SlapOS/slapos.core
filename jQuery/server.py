from flask import Flask
from flask import render_template, abort, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("slapos.html")

@app.route('/request', methods=["POST", "GET"]) 
def request():
    response = make_response("HELLO", 408)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response

if __name__ == '__main__':
    app.run(debug=True)