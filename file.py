from datetime import date
import re
from flask import Flask, request, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
from flask_pymongo import MongoClient
import urllib.parse
import jwt
import datetime
from functools import wraps
import json as jsonmodule
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5500", "http://127.0.0.1:5500/"], supports_credentials=True)

username = urllib.parse.quote_plus('falshami2002')
password = urllib.parse.quote_plus('M4gLrURtaBBKPoYv')
address = ("mongodb+srv://%s:%s@cluster0.6n6sslp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0" % (username, password))
mongo = MongoClient(address)
app.config['SECRET_KEY'] = "random"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.cookies:
            token = request.cookies["Authorization"]
            try:
                token = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
                return f(token, *args, **kwargs)
            except:
                return "Invalid Token", 401
        else:
            return "Login to get a token", 401

    return decorated

@app.route('/team/<string:teamname>', methods=['GET'])
@token_required
def get_user_by_name(token, teamname):
    parameters = ['team', 'player', 'injury', 'returnDate']
    if(request.headers.get('order') in parameters):
        order = request.headers.get('order')
        players = mongo.db.injuries.find({"team": teamname}).sort(order)
    elif(request.headers.get('order')):
        res = Response('Invalid order header')
        res.headers['invalid-header'] = request.headers.get('order')
        res.status = 400
        return res
    else:
        players = mongo.db.injuries.find({"team": teamname})
    data = []
    while(True):
        try:
            data.append(players.next())
        except StopIteration:
            break
    if data!=None and len(data) != 0:
        injuries = []
        for d in data:
            injuries.append("{player}, {team}, {injury}, {returnDate}\n".format(**d)) 
        
        res = Response(injuries)
        res.status = 200
        return res
    res = Response('Invalid Team')
    res.headers['invalid-team'] = teamname
    res.status = 400
    return res

@app.route('/add-injuries', methods=['POST'])
@token_required
def addInjuries(token):
    if request.args.get('method') == 'JSON':
        json = jsonmodule.loads(request.get_json(force=True))
        mongo.db.injuries.insert_many(json)
        res = Response("Your JSON data has been inserted")
        res.status = 200
        return res
    elif request.args.get('method') == 'form':
        player = request.form.get('player')
        team = request.form.get('team')
        injury = request.form.get('injury')
        returnDate = request.form.get('returnDate')
        mongo.db.injuries.insert_one({"player": player, "team": team, "injury": injury, "returnDate": returnDate})
        res = Response("Your form data has been inserted")
        res.status = 200
        return res
    elif request.args.get('method') == 'file':
        file = request.files['file']   
        print(file)     
        myFile = jsonmodule.loads(file.read())
        for injury in myFile:
            mongo.db.injuries.insert_one({"player": injury.get("player"), "team": injury.get("team"), "injury": injury.get("injury"), "returnDate": injury.get("returnDate")})
        res = Response("Your file data has been inserted")
        res.status = 200
        return res
    res = Response("Invalid Method")     
    res.status = 400
    return res

@app.route('/login', methods =['POST'])
def login():
    account=''
    msg = ''
    if request.method == 'POST' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        account = mongo.db.users.find_one({"username": username, "password": password})
        if account:
            token = jwt.encode({
            'public_id': str(account["_id"]),
            'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes = 30)
            }, app.config['SECRET_KEY'])
            res = Response(token)
            res.headers['current-user'] = account['username']
            res.set_cookie("Authorization", token)
            res.status = 200
            return res
        else:
            res = Response("Invalid Login")
            res.status = 300
            return res
    else:  
        res = Response('Missing Information')
        res.status = 400
        return res

@app.route('/register', methods =['POST'])
def register():
    msg = ''
    if request.method == 'POST'  and request.args.get('username') and request.args.get('password') and request.args.get('email'):
        username = request.args.get('username')
        password = request.args.get('password')
        email = request.args.get('email')
        account = mongo.db.users.find_one({"username": username})
        if account:
            res = Response('Account already exists !')
            res.status = 400
            return res
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            res = Response('Invalid email address !')
            res.status = 400
            return res
        elif not re.match(r'[A-Za-z0-9]+', username):
            res = Response('name must contain only characters and numbers !')
            res.status = 400
            return res
        else:
            mongo.db.users.insert_one({"username": username, "password": password, "email": email})
            res = Response('You have successfully registered!')
            return res
    if request.method == 'GET':
        res = Response("Wrong username / password, you have been redirected to the register endpoint to create an account")
        res.status = 300
        return res
    else:  
        res = Response('Missing Information')
        res.status = 400
        return res

@app.route('/delete-account', methods =['DELETE'])
@token_required
def deleteAccount(token):
    account=''
    msg = ''
    if request.method == 'DELETE' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        account = mongo.db.users.find_one({"username": username, "password": password})
        if account:
            if(token.get("public_id") != str(account.get("_id"))):
                msg = "You can only delete your own account"
                return msg, 401
            mongo.db.users.delete_one({"username": username, "password": password})
            msg = 'Your account has been deleted'
            return msg, 200
        else:
            msg = 'No account exists with this username and password'
            return msg, 400
    else:  
        msg = 'Missing Information'
        return msg, 400
    
@app.route('/change-account-info', methods =['PUT'])
@token_required
def changeAccountInfo(token):
    account=''
    msg = ''   
    if request.method == 'PUT' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        account = mongo.db.users.find_one({"username": username, "password": password})
        if(account and token.get("public_id") != str(account.get("_id"))):
            res = Response("You can only change your own account info")
            res.status = 401
            return res
        if account:
            if request.headers.get('new-username') and request.headers.get('new-password'):
                newUsername = request.headers.get('new-username')
                newPassword = request.headers.get('new-password')
                mongo.db.users.update_one(account, {"$set": {"username": newUsername, "password": newPassword}})
                res = Response(f'Username updated to {newUsername}\nPassword updated')
                res.status = 200
                return res
            elif request.headers.get('new-username'):
                newUsername = request.headers.get('new-username')
                mongo.db.users.update_one(account, {"$set": {"username": newUsername}})
                res = Response(f'Username updated to {newUsername}')
                res.status = 200
                return res
            elif request.headers.get('new-password'):
                newPassword = request.headers.get('new-password')
                mongo.db.users.update_one(account, {"$set": {"password": newPassword}})
                res = Response('Password updated')
                res.status = 200
                return res
            else:
                res = Response('No information was provided to update')
                res.status = 400
                return res
        else:
            res = Response('Incorrect username / password!')
            res.status = 400
            return res
    else:  
        res = Response('Missing Information')
        res.status = 400
        return res

if __name__ == '__main__':
    import sys
    port = 5000
    while True:
        try:
            app.run(host='0.0.0.0', port=port, debug=True)
        except OSError as e:
            if e.errno == 48:  # Address already in use
                port += 1
                continue
            else:
                print(f"Error: {e}")
                sys.exit(1)
