from flask import Flask, request, make_response
from functools import wraps

app = Flask(__name__)

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth and auth.username == 'username1' and auth.password == 'password':
            return f(*args, **kwargs)

        return make_response('Could not verify!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    return decorated

@app.route("/")
def index():
    if request.authorization and request.authorization.username == 'username1' and request.authorization.password == 'password':
        return '<h1>You are logged in</h1>'

    return make_response('Could not verify!',401,{'WWW-Authenticate': 'Basic realm="Login Required"'})

@app.route('/page')
@auth_required
def page():
    return '<h1>you are on the page!</h1>'

@app.route("/user/<username>")
@auth_required
def get_user(username):
    return {'username':username}


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True,port=8081)