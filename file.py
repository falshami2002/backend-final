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
    cur = mysql.connection.cursor()
    select_stmt = "SELECT * FROM injuries WHERE team = %(tname)s"
    cur.execute(select_stmt, {'tname': teamname})
    data = cur.fetchall()
    if data!=None and len(data) != 0:
        injuries = []
        for d in data:
            injuries.append("{player}, {team}, {injury}, {returnDate}".format(**d)) 
        return injuries
    return "Team Not Found", 400

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
            res = Response('Incorrect username / password !')
            res.status = 400
            return res
    else:  
        msg = 'Missing Information'
        return msg, 400

@app.route('/register', methods =['POST'])
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
