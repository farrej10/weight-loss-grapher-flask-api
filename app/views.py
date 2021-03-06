from app import app
from flask import render_template, request, make_response, url_for, redirect, flash
from flask_limiter import Limiter, HEADERS
from flask_limiter.util import get_remote_address

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
mysql = None

limiter = Limiter(
    app,
    key_func=get_remote_address,
    storage_uri="redis://redis:6379",
    headers_enabled=True,
    default_limits=["1000 per day", "50 per hour"]
)
limiter.header_mapping = {
    HEADERS.LIMIT: "X-My-Limit",
    HEADERS.RESET: "X-My-Reset",
    HEADERS.REMAINING: "X-My-Remaining"
}

load_dotenv()
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['JSON_SORT_KEYS'] = False

websitepath = os.environ.get('WEBPATH')
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
            mysqlcommand = "SELECT user_id,name,admin,email FROM weightlossgrapher.user WHERE user_id = %s;"
            try:
                cur.execute(mysqlcommand, (data['user_id'],))
            except Exception as e:
                # If this fails its likely an error related to connection to mysql or lack there of
                return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR
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
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        links = "{path}/user/{id}/weights/{time}"
        if (len(results) <= 1):
            link = links.format(
                path=websitepath, id=results[0]['timestamp'], time=results[0]['timestamp'].replace(" ", "T"))
            results[0]['_links'] = {'self': {'href': link}}
            return jsonify(results[0]), status.HTTP_200_OK
            return jsonify(results[0]), status.HTTP_200_OK
        else:
            for idc, i in enumerate(results):
                link = links.format(
                    path=websitepath, id=i['user_id'], time=results[idc]['timestamp'].replace(" ", "T"))
                results[idc]['_links'] = {'self': {'href': link}}
            return jsonify(results), status.HTTP_200_OK


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
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        links = "{path}/user/{id}/weights/{time}"
        if (len(results) <= 1):
            link = links.format(path=websitepath, id=user_id,
                                time=results[0]['timestamp'].replace(" ", "T"))
            results[0]['_links'] = {'self': {'href': link}}
            return jsonify(results[0]), status.HTTP_200_OK
            return jsonify(results[0]), status.HTTP_200_OK
        else:
            for idc, i in enumerate(results):
                link = links.format(
                    path=websitepath, id=i['user_id'], time=results[idc]['timestamp'].replace(" ", "T"))
                results[idc]['_links'] = {'self': {'href': link}}
            return jsonify(results), status.HTTP_200_OK

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
        sql = """SELECT t1.user_id, name, CAST(timestamp AS CHAR(30)), weight FROM user t1 INNER JOIN weights t2 ON t1.user_id = t2.user_id WHERE name = %s AND timestamp BETWEEN  %s AND %s ORDER BY timestamp;"""
        cur.execute(sql, (name, start, end))
    except Exception as e:
        # Using 400 as its likely a bad request
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[2] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()

    if(results):
        links = "{path}/user/{id}/weights/{time}"
        if (len(results) <= 1):
            link = links.format(
                path=websitepath, id=results[0]['timestamp'], time=results[0]['timestamp'].replace(" ", "T"))
            results[0]['_links'] = {'self': {'href': link}}
            return jsonify(results[0]), status.HTTP_200_OK
            return jsonify(results[0]), status.HTTP_200_OK
        else:
            for idc, i in enumerate(results):
                link = links.format(
                    path=websitepath, id=i['user_id'], time=results[idc]['timestamp'].replace(" ", "T"))
                results[idc]['_links'] = {'self': {'href': link}}
            return jsonify(results), status.HTTP_200_OK


# Create a weight entry for a user
@token_required
def create_weight_for_user(current_user, request):

    user_id = None
    weight = None
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(
        ts).strftime('%Y-%m-%d %H:%M:%S')

    if(request.form.get('weight', None) != None):
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
    content = dict(user=user_id, timestamp=timestamp, weight=weight)

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO `weightlossgrapher`.`weights` (`user_id`,`timestamp`,`weight`) VALUES (%s,%s,%s);", (user_id, timestamp, weight))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

    cur.close()

    links = "{path}/user/{id}/weights/{time}"
    link = links.format(
        path=websitepath, id=user_id, time=timestamp.replace(" ", "T"))
    content['_links'] = {'self': {'href': link}}
    return jsonify(content), status.HTTP_201_CREATED


@token_required
def get_users(current_user, id, name):

    if(current_user[2] != 1 and current_user[0] != id):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    mysqlcommand = ""
    searchparam = ""
    if(id != None):
        mysqlcommand = "SELECT user_id,name,admin,email FROM weightlossgrapher.user WHERE user_id = %s;"
        searchparam = id
    elif(name != None):
        mysqlcommand = "SELECT user_id,name,admin,email FROM weightlossgrapher.user WHERE name = %s;"
        searchparam = name
    else:
        mysqlcommand = "SELECT user_id,name,admin,email FROM weightlossgrapher.user;"
    try:
        if(searchparam == ""):
            cur.execute(mysqlcommand)
        else:
            cur.execute(mysqlcommand, (searchparam,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results):
        links = "{path}/user/{id}"
        if (len(results) <= 1):
            link = links.format(path=websitepath, id=id)
            results[0]['_links'] = {'self': {'href': link}}
            return jsonify(results[0]), status.HTTP_200_OK
            return jsonify(results[0]), status.HTTP_200_OK
        else:
            for idc, i in enumerate(results):
                link = links.format(path=websitepath, id=i['user_id'])
                results[idc]['_links'] = {'self': {'href': link}}
            return jsonify(results), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


@token_required
def create_user(current_user):

    if(current_user[2] != 1):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    # Check if request has json and has the two required fields
    if not request.json or not 'name' in request.json or not 'email' in request.json or not 'pass' in request.json or not 'admin' in request.json:
        return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST

    # extract content
    content = request.json
    user = None
    if 'user_id' in content:
        user = content['user_id']
    name = content['name']
    email = content['email']
    pwd = content['pass']
    admin = content['admin']

    password = str.encode(pwd)
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)

    cur = mysql.connection.cursor()
    if user == None:
        try:
            cur.execute(
                "INSERT INTO `weightlossgrapher`.`user` (`name`,`email`,`pass`,`admin`) VALUES (%s,%s,%s,%s);", (name, email, hashed, admin))
            cur.execute(
                "SELECT user_id,name,admin,email FROM `weightlossgrapher`.`user` WHERE `user_id`= LAST_INSERT_ID()")
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

        fields = [i[0] for i in cur.description]
        results = [dict(zip(fields, row)) for row in cur.fetchall()]

        cur.close()
        links = "{path}/user/{id}"
        link = links.format(path=websitepath, id=results[0]['user_id'])
        results[0]['_links'] = {'self': {'href': link}}
        return jsonify(results[0]), status.HTTP_201_CREATED
    else:
        try:
            cur.execute(
                "INSERT INTO `weightlossgrapher`.`user` (`user_id`,`name`,`email`,`pass`,`admin`) VALUES (%s,%s,%s,%s,%s);", (user,name, email, hashed, admin))
            cur.execute(
                "SELECT user_id,name,admin,email FROM `weightlossgrapher`.`user` WHERE `user_id`= %s", (user,))
            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

        fields = [i[0] for i in cur.description]
        results = [dict(zip(fields, row)) for row in cur.fetchall()]

        cur.close()
        links = "{path}/user/{id}"
        link = links.format(path=websitepath, id=results[0]['user_id'])
        results[0]['_links'] = {'self': {'href': link}}
        return jsonify(results[0]), status.HTTP_201_CREATED


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


@app.route('/user/<int:id>/weights/<string:timestamp>', methods=['GET'])
@token_required
def exactweight(current_user, id, timestamp):
    if(current_user[2] != 1 and current_user[0] != id):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s AND timestamp = %s;"
    try:
        cur.execute(mysqlcommand, (id, timestamp))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    links = "{path}/user/{id}/weights/{timestamp}"
    link = links.format(path=websitepath, id=id, timestamp=timestamp)
    if(results):
        results[0]['_links'] = {'self': {'href': link}}
        return jsonify(results[0]), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


@app.route('/user', defaults={"id": None}, methods=['GET', 'POST'])
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


@app.route('/user/<int:id>/weights/<string:timestamp>', methods=['DELETE'])
@token_required
def deleteExactWeight(current_user, id, timestamp):
    if(current_user[2] != 1 and current_user[0] != id):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s AND timestamp = %s;"
    try:
        cur.execute(mysqlcommand, (id, timestamp))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    fields[1] = 'timestamp'  # change field name
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results):
        cur = mysql.connection.cursor()
        mysqlcommand = "DELETE FROM weights WHERE user_id = %s AND timestamp = %s;"
        try:
            cur.execute(mysqlcommand, (id, timestamp))
            mysql.connection.commit()
        except Exception as e:
            # If this fails its likely an error related to connection to mysql or lack there of
            return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR
        cur.close()
        return jsonify(message="Successfully Deleted"), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND

@app.route('/user/<int:id>', methods=['DELETE'])
@token_required
def deleteUser(current_user, id):
    if(current_user[2] != 1 and current_user[0] != id):
        return jsonify({'error': 'Not Admin'}), status.HTTP_401_UNAUTHORIZED

    cur = mysql.connection.cursor()
    mysqlcommand = """SELECT user_id,name FROM weightlossgrapher.user WHERE user_id = %s;"""
    try:
        cur.execute(mysqlcommand, (id,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results):
        cur = mysql.connection.cursor()
        mysqlcommand = """DELETE FROM user WHERE user_id = %s;"""
        try:
            cur.execute(mysqlcommand, (id, ))
            mysql.connection.commit()
        except Exception as e:
            # If this fails its likely an error related to connection to mysql or lack there of
            return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR
        cur.close()
        return jsonify(message="Successfully Deleted"), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND

@app.route('/current-user', methods=['GET'])
@token_required
def current_user(current_user):
    user_info = dict(
        user_id=current_user[0], name=current_user[1], admin=current_user[2],email=current_user[3])
    links = "{path}/user/{id}"
    link = links.format(path=websitepath, id=current_user[0])
    user_info['_links'] = {'self': {'href': link}}
    return jsonify(user_info), status.HTTP_200_OK


@app.route('/auth', methods=['GET'])
@limiter.limit("20 per hour")
def auth():
    auth = request.authorization

    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT pass FROM weightlossgrapher.user WHERE user_id = %s;"
    id = auth['username']
    passwd = auth['password']
    try:
        cur.execute(mysqlcommand, (id,))
    except Exception as e:
        # If this fails its likely an error related to connection to mysql or lack there of
        return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

    fields = [i[0] for i in cur.description]
    results = [dict(zip(fields, row)) for row in cur.fetchall()]
    cur.close()
    if(results == []):
        return jsonify({'error': 'Incorrect Password or User-ID'}), status.HTTP_401_UNAUTHORIZED

    db_hashed = results[0]['pass'].decode('utf-8').rstrip('\x00')

    if (not bcrypt.checkpw(passwd.encode('utf-8'), db_hashed.encode('utf-8'))):
        return jsonify({'error': 'Incorrect Password or User-ID'}), status.HTTP_401_UNAUTHORIZED

    token = jwt.encode({'user_id': id, 'exp': datetime.datetime.utcnow(
    ) + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'], algorithm='HS256')

    resp = make_response(jsonify({'message': 'Login Sucessful'}))
    resp.set_cookie('token', token, httponly=True, secure=True,
                    samesite='Strict', max_age=datetime.timedelta(minutes=10))
    return resp, status.HTTP_200_OK


@app.route('/auth', methods=['POST'])
@limiter.limit("20 per hour")
def auth_and_redirect():
    auth = request.form
    cur = mysql.connection.cursor()
    mysqlcommand = "SELECT pass,user_id FROM weightlossgrapher.user WHERE email = %s;"
    if (request.form.get('uname', None) != None):
        email = auth['uname']
        passwd = auth['psw']
        try:
            cur.execute(mysqlcommand, (email,))
        except Exception as e:
            # If this fails its likely an error related to connection to mysql or lack there of
            return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

        fields = [i[0] for i in cur.description]
        results = [dict(zip(fields, row)) for row in cur.fetchall()]
        cur.close()
        if(results == []):
            return redirect('login'), status.HTTP_302_FOUND

        db_hashed = results[0]['pass'].decode('utf-8').rstrip('\x00')
        if (not bcrypt.checkpw(passwd.encode('utf-8'), db_hashed.encode('utf-8'))):
            return redirect('login'), status.HTTP_302_FOUND

        token = jwt.encode({'user_id': results[0]['user_id'], 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'], algorithm='HS256')

        resp = make_response(redirect('index'))
        resp.set_cookie('token', token, httponly=True, secure=True,
                        samesite='Strict', max_age=datetime.timedelta(minutes=10))
        return resp, status.HTTP_302_FOUND
    else:
        if not request.json or not 'email' in request.json or not 'pass' in request.json:
            return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST
        content = request.json
        email = content['email']
        passwd = content['pass']
        try:
            cur.execute(mysqlcommand, (email,))
        except Exception as e:
            # If this fails its likely an error related to connection to mysql or lack there of
            return jsonify(error=str(e[0])), status.HTTP_500_INTERNAL_SERVER_ERROR

        fields = [i[0] for i in cur.description]
        results = [dict(zip(fields, row)) for row in cur.fetchall()]
        cur.close()
        if(results == []):
            return jsonify({'error': 'Incorrect Password or User-ID'}), status.HTTP_401_UNAUTHORIZED

        db_hashed = results[0]['pass'].decode('utf-8').rstrip('\x00')
        if (not bcrypt.checkpw(passwd.encode('utf-8'), db_hashed.encode('utf-8'))):
            return jsonify({'error': 'Incorrect Password or User-ID'}), status.HTTP_401_UNAUTHORIZED

        token = jwt.encode({'user_id': results[0]['user_id'], 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=10)}, app.config['SECRET_KEY'], algorithm='HS256')
        resp = make_response(jsonify({'message': 'Login Sucessful'}))
        resp.set_cookie('token', token, httponly=True, secure=True,
                        samesite='Strict', max_age=datetime.timedelta(minutes=10))
        return resp, status.HTTP_200_OK


if __name__ == '__main__':
    app.run(debug=True)
