from flask import Flask
from flask import render_template, abort, request, make_response
app = Flask(__name__)

@app.route('/')
def index():
    return "index"
    
@app.route('/test-mobile')
def test():
    return render_template('test-mobile.html')

@app.route('/request', methods=["POST", "GET"]) 
def request():
    response = make_response("HELLO", 409)
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    return response

if __name__ == '__main__':
    app.run(debug=True)