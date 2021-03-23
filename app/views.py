from app import app
from flask import render_template, request, make_response, url_for, redirect, flash

from flask_api import status
from flask import jsonify

import pdb
import json
import sys

import time
import datetime
import jwt
import bcrypt
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash

from dotenv import load_dotenv
import os
from flask_mysqldb import MySQL

# authtoken
mysql=None


load_dotenv()
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

mysql = MySQL(app)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            cur = mysql.connection.cursor()
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms=['HS256'])
            mysqlcommand = "SELECT id,name,admin FROM weightlossgrapher.user WHERE id = %s;"
            try:
                cur.execute(mysqlcommand, (data['id'],))
            except Exception as e:
                # If this fails its likely an error related to connection to mysql or lack there of
                return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR
            current_user = cur.fetchone()
        except:
            return jsonify({'error': 'Token Expired'}), status.HTTP_401_UNAUTHORIZED

        return f(current_user, *args, **kwargs)

    return decorated


@token_required
def get_weigths(current_user, start, end):  # Return weights table

    if(current_user[2] != 1):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE timestamp BETWEEN  %s AND %s ORDER BY timestamp;", (start, end))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        return jsonify(results), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


@token_required
# Return all weights for a user
def get_weights_by_user(current_user, user_id, start, end):
    
    if (current_user[0] != user_id) and (current_user[2] != 1):
        return jsonify(error="UNAUTHORIZED"), status.HTTP_401_UNAUTHORIZED
    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s AND timestamp BETWEEN  %s AND %s ORDER BY timestamp;", (user_id, start, end))
    except Exception as e:
        # Using 400 as its likely a bad request
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        return jsonify(results), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


@token_required
# return all weights for a user's name
def get_weights_by_name(current_user, name, start, end):
    if(current_user[2] != 1):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id, name, CAST(timestamp AS CHAR(30)), weight FROM user t1 INNER JOIN weights t2 ON t1.id = t2.user_id WHERE name = %s AND timestamp BETWEEN  %s AND %s ORDER BY timestamp;", (name, start, end))
    except Exception as e:
        # Using 400 as its likely a bad request
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[2] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        return jsonify(results), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


# Create a weight entry for a user
@token_required
def create_weight_for_user(current_user, request):

    user_id = None
    weight = None
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(
        ts).strftime('%Y-%m-%d %H:%M:%S')
    
    if(request.form != None):
        data = request.form
        user_id = current_user[0]
        weight = data['weight']
        timestamp = data['timestamp']
    else:
        # Check if request has json and has the two required fields
        if not request.json or not 'user_id' in request.json or not 'weight' in request.json:
            return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST

    # extract content + make timestamp
        content = request.json
        user_id = content['user_id']
        weight = content['weight']
        if (not 'timestamp' in request.json):
            ts = time.time()
            timestamp = datetime.datetime.fromtimestamp(
                ts).strftime('%Y-%m-%d %H:%M:%S')
        else:
            timestamp = content['timestamp']

    if (current_user[0] != user_id and current_user[2] != 1):
        return jsonify(error="UNAUTHORIZED"), status.HTTP_401_UNAUTHORIZED

    # add the generated timestamp used for response
    content = dict(user=user_id,timestamp=timestamp,weight=weight)

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO `weightlossgrapher`.`weights` (`user_id`,`timestamp`,`weight`) VALUES (%s,%s,%s);", (user_id, timestamp, weight))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

    cur.close()
    return jsonify(content), status.HTTP_201_CREATED


@token_required
def get_users(current_user, id, name):

    if(current_user[2] != 1 and current_user[0] != id):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    mysqlcommand = ""
    searchparam = ""
    if(id != None):
        mysqlcommand = "SELECT id,name,admin,email FROM weightlossgrapher.user WHERE id = %s;"
        searchparam = id
    elif(name != None):
        mysqlcommand = "SELECT id,name,admin,email FROM weightlossgrapher.user WHERE name = %s;"
        searchparam = name
    else:
        mysqlcommand = "SELECT id,name,admin,email FROM weightlossgrapher.user;"
    try:
        if(searchparam == ""):
            cur.execute(mysqlcommand)
        else:
            cur.execute(mysqlcommand, (searchparam,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results):
        return jsonify({'users': results}), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


@token_required
def create_user(current_user):

    if(current_user[2] != 1):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    # Check if request has json and has the two required fields
    if not request.json or not 'name' in request.json:
        return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST

    # extract content + make timestamp
    content = request.json
    name = content['name']

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO `weightlossgrapher`.`user` (`name`) VALUES (%s);", (name,))
        cur.execute(
            "SELECT * FROM `weightlossgrapher`.`user` WHERE `id`= LAST_INSERT_ID()")
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]

    cur.close()
    return jsonify(results), status.HTTP_201_CREATED


@app.route('/weights', methods=['GET', 'POST'])
def weights():

    if request.method == "GET":
        paramslist = list(request.args.to_dict().keys())
        if 'user' in paramslist:
            paramslist.remove('user')
        if 'name' in paramslist:
            paramslist.remove('name')
        if 'start' in paramslist:
            paramslist.remove('start')
        if 'end' in paramslist:
            paramslist.remove('end')
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        user = request.args.get('user', default=None, type=int)
        name = request.args.get('name', default=None, type=str)
        start = request.args.get(
            'start', default='1970-01-01 12:00:00', type=str)
        now = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y-%m-%d %H:%M:%S')
        end = request.args.get('end', default='2050-01-01 12:00:00', type=str)

        if(end != now):
            end += " 23:59:59"

        if(start == end):
            start += " 00:00:00"
            end += " 23:59:59"
        # user is unique therfore select based on that
        if (user != None):
            return get_weights_by_user(user, start, end)
        if (name != None):
            return get_weights_by_name(name, start, end)
        else:
            return get_weigths(start, end)

    if request.method == "POST":
        # should be no params all info should be in the body
        paramslist = list(request.args.to_dict().keys())
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        return create_weight_for_user(request)

@app.route('/user/',defaults={"id":None})
@app.route('/user/<int:id>', methods=['GET', 'POST'])
def user(id):

    if request.method == "GET":
        paramslist = list(request.args.to_dict().keys())

        if 'name' in paramslist:
            paramslist.remove('name')
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        else:
            user = id
            name = request.args.get('name', default=None, type=str)
            return get_users(user, name)

    if request.method == "POST":
        # should be no params all info should be in the body
        paramslist = list(request.args.to_dict().keys())
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        else:
            return create_user()

@app.route('/user/<int:id>/weights', methods=['GET'])
def weights_1(id):
    paramslist = list(request.args.to_dict().keys())
    if 'start' in paramslist:
        paramslist.remove('start')
    if 'end' in paramslist:
        paramslist.remove('end')
    if(paramslist):
        return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
    user = id
    start = request.args.get(
        'start', default='1970-01-01 12:00:00', type=str)
    now = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y-%m-%d %H:%M:%S')
    end = request.args.get('end', default='2050-01-01 12:00:00', type=str)

    if(end != now):
        end += " 23:59:59"

    if(start == end):
        start += " 00:00:00"
        end += " 23:59:59"
    # user is unique therfore select based on that
    return get_weights_by_user(user, start, end)


@app.route('/current-user', methods=['GET'])
@token_required
def current_user(current_user):
    user_info = dict(
        id=current_user[0], name=current_user[1], admin=current_user[2])
    return jsonify(user_info), status.HTTP_200_OK


@app.route('/auth', methods=['GET'])
def auth():
    auth = request.authorization
    
    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT pass FROM weightlossgrapher.user WHERE id = %s;"
    id = auth['username']
    passwd = auth['password']
    try:
        cur.execute(mysqlcommand, (id,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    db_hashed = results[0]['pass'].decode('utf-8').rstrip('\x00')

    if (not bcrypt.checkpw(passwd.encode('utf-8'), db_hashed.encode('utf-8'))):
        return jsonify({'error': 'Incorrect Password or User-ID'}), status.HTTP_401_UNAUTHORIZED

    token = jwt.encode({'id': id, 'exp': datetime.datetime.utcnow(
    ) + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'], algorithm='HS256')

    resp = make_response(jsonify({'message': 'Login Sucessful'}))
    resp.set_cookie('token', token)#, httponly=True, secure=True)
    return resp, status.HTTP_200_OK


@app.route('/auth', methods=['POST'])
def auth_and_redirect():
    auth = request.form
    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT pass,id FROM weightlossgrapher.user WHERE email = %s;"
    email = auth['uname']
    passwd = auth['psw']
    try:
        cur.execute(mysqlcommand, (email,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e)), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results == []):
        return redirect('login'), status.HTTP_302_FOUND

    db_hashed = results[0]['pass'].decode('utf-8').rstrip('\x00')
    if (not bcrypt.checkpw(passwd.encode('utf-8'), db_hashed.encode('utf-8'))):
        return redirect('login'), status.HTTP_302_FOUND

    token = jwt.encode({'id': results[0]['id'], 'exp': datetime.datetime.utcnow(
    ) + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'], algorithm='HS256')

    resp = make_response(redirect('index'))
    resp.set_cookie('token', token, httponly=True, secure=True,
                    samesite='Strict', max_age=datetime.timedelta(minutes=10))
    return resp, status.HTTP_302_FOUND


#@app.route('/tmp')
def temp():
    password = b"KWS4FOID9o"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)

    cur = mysql.connection.cursor()
    mysqlcommand = "UPDATE `weightlossgrapher`.`user` SET `pass` = %s WHERE `id` = 28;"
    param = hashed
    try:
        cur.execute(mysqlcommand, (param,))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({'error': str(e)}), status.HTTP_500_INTERNAL_SERVER_ERROR

    return jsonify({'message': 'success'}), status.HTTP_200_OK


if __name__ == '__main__':
    app.run(debug=True)
