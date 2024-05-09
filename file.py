from datetime import date
import re
from flask import Flask, request, render_template, redirect, url_for, Response
from flask_pymongo import PyMongo
from flask_pymongo import MongoClient
import urllib.parse
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
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
                return redirect(url_for('login'))
        else:
            return redirect(url_for('login'))

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
            injuries.append("{player}, {team}, {injury}, {returnDate}".format(**d)) 
        return injuries, 200
    res = Response('Invalid Team')
    res.headers['invalid-team'] = teamname
    res.status = 400
    return res

@app.route('/add-injuries', methods=['POST'])
def addInjuries():
    cur = mysql.connection.cursor()
    msg = ''
    if request.args.get('method') == 'JSON':
        json = request.get_json()
        for injury in json:
            cur.execute('INSERT INTO injuries VALUES (%s, %s, %s, %s)', (injury.get('player'), injury.get('team'), injury.get('injury'), injury.get('returnDate')))
        mysql.connection.commit()
        msg = "Your JSON data has been inserted"
        return msg, 200
    elif request.args.get('method') == 'form':
        player = request.form.get('player')
        team = request.form.get('team')
        injury = request.form.get('injury')
        returnDate = request.form.get('returnDate')
        cur.execute('INSERT INTO injuries VALUES (%s, %s, %s, %s)', (player, team, injury, returnDate))
        mysql.connection.commit()
        msg = "Your form data has been inserted"
        return msg, 200
    msg = "Invalid Method"
    return msg, 400

@app.route('/login', methods =['POST'])
def login():
    account=''
    msg = ''
    if request.method == 'POST' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        account = mongo.db.users.find_one({"username": username, "password": password})
        if account:
            res = Response('Logged in successfully')
            res.headers['current-user'] = account['username']
            res.status = 200
            print(account)
            token = jwt.encode({
            'public_id': str(account["_id"]),
            'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes = 30)
            }, app.config['SECRET_KEY'])
            res = Response(token)
            res.set_cookie("Authorization", token)
            res.status = 200
            return res
        else:
            return redirect(url_for('register')), 300
    else:  
        msg = 'Missing Information'
        return msg, 400

@app.route('/register', methods =['POST', 'GET'])
def register():
    msg = ''
    if request.method == 'POST'  and request.args.get('username') and request.args.get('password') and request.args.get('email'):
        username = request.args.get('username')
        password = request.args.get('password')
        email = request.args.get('email')
        account = mongo.db.users.find_one({"username": username})
        if account:
            msg = 'Account already exists !'
            return msg, 400
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
            return msg, 400
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
            return msg, 400
        else:
            mongo.db.users.insert_one({"username": username, "password": password, "email": email})
            msg = 'You have successfully registered!'
            return msg, 200
    if request.method == 'GET':
        msg = "Wrong username / password, you have been redirected to the register endpoint to create an account"
        return msg, 300
    else:  
        msg = 'Missing Information'
        return msg, 400

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
                return msg, 400
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
def changeAccountInfo():
    cur = mysql.connection.cursor()
    account=''
    msg = ''
    if request.method == 'PUT' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        cur.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password ))
        account = cur.fetchone()
        if account:
            if request.headers.get('new-username') and request.headers.get('new-password'):
                newUsername = request.headers.get('new-username')
                newPassword = request.headers.get('new-password')
                cur.execute('UPDATE accounts SET username = % s, password = % s WHERE username = % s', (newUsername, newPassword, account['username']))
                mysql.connection.commit()
                msg = f'Username updated to {newUsername}\nPassword updated'
                return msg, 200
            elif request.headers.get('new-username'):
                newUsername = request.headers.get('new-username')
                cur.execute('UPDATE accounts SET username = % s WHERE username = % s', (newUsername, account['username']))
                mysql.connection.commit()
                msg = f'Username updated to {newUsername}'
                return msg, 200
            elif request.headers.get('new-password'):
                newPassword = request.headers.get('new-password')
                cur.execute('UPDATE accounts SET password = % s WHERE username = % s', (newPassword, account['username']))
                mysql.connection.commit()
                msg = 'Password updated'
                return msg, 200
            else:
                msg = 'No information was provided to update'
                return msg, 400
        else:
            msg = 'Incorrect username / password!'
            return msg, 400
    else:  
        msg = 'Missing Information'
        return msg, 400

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
