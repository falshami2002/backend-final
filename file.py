from datetime import date
import re
from flask import Flask, request, render_template
from flask_mysqldb import MySQL

app = Flask(__name__)

app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD']='test@123'
app.config['MYSQL_HOST']='localhost'
app.config['MYSQL_DB']='user'
# app.config['MYSQL_CURSORCLASS']='DictCursor'

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

@app.route('/user/<string:username>')
def get_user_by_name(username):
    cur = mysql.connection.cursor()
    select_stmt = "SELECT * FROM employees WHERE name = %(uname)s"
    cur.execute(select_stmt, {'uname': username})
    data = cur.fetchone()
    print(data)
    if data!=None:
        field_map = fields(cur)
        for row in field_map:
            print(row)
        row_res = dict(zip(field_map.keys(), data))
        return "{name}, {date}".format(**data)
    return "User Not Found", 400

@app.route('/login', methods =['GET', 'POST'])
def login():
    cur = mysql.connection.cursor()
    account=''
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cur.execute('SELECT * FROM accounts WHERE username = % s AND password = % s', (username, password ))
        account = cur.fetchone()
    if account:
        msg = 'Logged in successfully !'
        return render_template('index.html', msg=msg)
    else:
        msg = 'Incorrect username / password !'
        return render_template('register.html')
        # return ''' <form method="POST">
        #        <div><label>UserName: <input type="text" name="username"></label></div>
        #        <div><label>Password: <input type="text" name="password"></label></div>
        #        <input type="submit" value="Submit">
        #    </form>'''

@app.route('/register', methods =['GET', 'POST'])
def register():
    cur = mysql.connection.cursor()
    msg = ''
    if request.method == 'POST' and \
            'username' in request.form and 'password' in request.form and \
            'email' in request.form and 'address' in request.form and 'city' \
            in request.form and 'country' in request.form and 'postalcode' \
            in request.form and 'organisation' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        organisation = request.form['organisation']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        country = request.form['country']
        postalcode = request.form['postalcode']
        cur.execute('SELECT * FROM users WHERE username = % s', (username, ))
        account = cur.fetchone()
        if account:
            msg = 'Account already exists !'
            return msg
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address !'
            return msg
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'name must contain only characters and numbers !'
            return msg
        else:
            cur.execute('INSERT INTO users VALUES (% s, % s, % s, % s, % s, % s, % s, % s, % s)',
                        (username, password, email, organisation, address, city, state, country, postalcode,))
            mysql.connection.commit()
            msg = 'You have successfully registered !'
            return msg

    elif request.method == 'GET':
        msg = 'Please fill out the form !'
        return ''' <form method="POST">
                  <div><label>UserName: <input type="text" name="username"></label></div>
                  <div><label>Password: <input type="text" name="password"></label></div>
                  <div><label>Email: <input type="text" name="email"></label></div>
                  <div><label>Organisation: <input type="text" name="organisation"></label></div>
                  <div><label>Address: <input type="text" name="address"></label></div>
                  <div><label>City: <input type="text" name="city"></label></div>
                  <div><label>State: <input type="text" name="state"></label></div>
                  <div><label>Country: <input type="text" name="country"></label></div>
                  <div><label>Postalcode: <input type="text" name="postalcode"></label></div>
                  <input type="submit" value="Submit">
              </form>'''


if __name__=='__main__':
    app.run(host='0.0.0.0',debug=True)