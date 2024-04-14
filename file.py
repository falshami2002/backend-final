from datetime import date
import re
from flask import Flask, request, render_template, redirect, url_for, Response
from flask_mysqldb import MySQL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

app.config['MYSQL_USER'] = 'sql3691778'
app.config['MYSQL_PASSWORD'] = 'aqnKdjcJ9A'
app.config['MYSQL_HOST'] = 'sql3.freemysqlhosting.net'
app.config['MYSQL_DB'] = 'sql3691778'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

@app.route('/')
def index():
    cur = mysql.connection.cursor()
#     cur.execute('''CREATE PROCEDURE getusers()
# BEGIN
#   SELECT * FROM user.employees;
# END;
# ''')
    cur.callproc('getusers')
    # data = cur.fetchall()
    for result in cur.fetchall():
         print(result)
         print(f'Name: {result[0]}, Date: {result[1]}')
    # return render_template('data.html',data=data)
    cur.close()
    return "Procedure Done!"

@app.route('/add-users')
def add_users():
    cur = mysql.connection.cursor()
    data = [
        ('Jane', date(2005, 2, 12)),
        ('Joe', date(2006, 5, 23)),
        ('John', date(2010, 10, 3)),
    ]
    # cur.execute('''CREATE TABLE employees(name VARCHAR(50), date DATE)''')

    stmt = "INSERT INTO employees (name, date) VALUES (%s, %s)"
    cur.executemany(stmt,data)
    mysql.connection.commit()
    cur.close()
    return "Data Created!"

def fields(cursor):
    results = {}
    column = 0
    for d in cursor.description:
        print(d)
        results[d[0]] = column
        column = column + 1

    return results

@app.route('/team/<string:teamname>', methods=['GET'])
def get_user_by_name(teamname):
    parameters = ['team', 'player', 'injury', 'returnDate']
    cur = mysql.connection.cursor()
    if(request.headers.get('order') in parameters):
        order = request.headers.get('order')
        cur.execute("SELECT * FROM injuries WHERE team = %s ORDER BY " + order, (teamname,))
    elif(request.headers.get('order')):
        res = Response('Invalid order header')
        res.headers['invalid-header'] = request.headers.get('order')
        res.status = 400
        return res
    else:
        cur.execute("SELECT * FROM injuries WHERE team = %s", (teamname,))
    data = cur.fetchall()
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
    cur = mysql.connection.cursor()
    account=''
    msg = ''
    if request.method == 'POST' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        cur.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password ))
        account = cur.fetchone()
        if account:
            res = Response('Logged in successfully')
            res.headers['current-user'] = account['username']
            res.status = 200
            return res
        else:
            return redirect(url_for('register')), 300
    else:  
        msg = 'Missing Information'
        return msg, 400

@app.route('/register', methods =['POST', 'GET'])
def register():
    cur = mysql.connection.cursor()
    msg = ''
    if request.method == 'POST'  and request.args.get('username') and request.args.get('password') and request.args.get('email'):
        username = request.args.get('username')
        password = request.args.get('password')
        email = request.args.get('email')
        cur.execute('SELECT * FROM accounts WHERE username = % s', [username])
        account = cur.fetchone()
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
            cur.execute('INSERT INTO accounts VALUES (% s, % s, % s)',
                        (username, password, email))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            return msg, 200
    if request.method == 'GET':
        msg = "Wrong username / password, you have been redirected to the register endpoint to create an account"
        return msg, 300
    else:  
        msg = 'Missing Information'
        return msg, 400

@app.route('/delete-account', methods =['DELETE'])
def deleteAccount():
    cur = mysql.connection.cursor()
    account=''
    msg = ''
    if request.method == 'DELETE' and request.args.get('username') and request.args.get('password'):
        username = request.args.get('username')
        password = request.args.get('password')
        cur.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password ))
        account = cur.fetchone()
        if account:
            cur.execute('DELETE FROM accounts WHERE username = % s', ([account['username']]))
            mysql.connection.commit()
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
