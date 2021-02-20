from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask_api import status
from flask import jsonify
from dotenv import load_dotenv
import pdb
import json
import os
import time
import datetime

app = Flask(__name__)


load_dotenv()
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')

mysql = MySQL(app)


def get_weigths(start, end):  # Return weights table

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


def get_weights_by_user(user, start, end):  # Return all weights for a user

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s AND timestamp BETWEEN  %s AND %s ORDER BY timestamp;", (user, start, end))
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


def get_weights_by_name(name, start, end):  # return all weights for a user's name

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id, name, timestamp, weight FROM user t1 INNER JOIN weights t2 ON t1.id = t2.user_id WHERE name = %s AND timestamp BETWEEN  %s AND %s ORDER BY timestamp;", (name, start, end))
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


def create_weight_for_user(request):  # Create a weight entry for a user

    # Check if request has json and has the two required fields
    if not request.json or not 'user' in request.json or not 'weight' in request.json:
        return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST

    # extract content + make timestamp
    content = request.json
    user = content['user']
    weight = content['weight']
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(
        ts).strftime('%Y-%m-%d %H:%M:%S')
    # add the generated timestamp used for response
    content['timestamp'] = timestamp

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "INSERT INTO `weightlossgrapher`.`weights` (`user_id`,`timestamp`,`weight`) VALUES (%s,%s,%s);", (user, timestamp, weight))
        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        return jsonify(error=str(e)), status.HTTP_400_BAD_REQUEST

    cur.close()
    return jsonify(content), status.HTTP_201_CREATED


def get_users(id, name):  # Return weights table

    cur = mysql.connection.cursor()
    mysqlcommand = ""
    searchparam = ""
    if(id != None):
        mysqlcommand = "SELECT * FROM weightlossgrapher.user WHERE id = %s;"
        searchparam = id
    elif(name != None):
        mysqlcommand = "SELECT * FROM weightlossgrapher.user WHERE name = %s;"
        searchparam = name
    else:
        mysqlcommand = "SELECT * FROM weightlossgrapher.user;"
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
        return jsonify(results), status.HTTP_200_OK
    else:
        return jsonify(error="Not Found"), status.HTTP_404_NOT_FOUND


def create_user():
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


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


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
        user = request.args.get('user', default=None, type=str)
        name = request.args.get('name', default=None, type=str)
        start = request.args.get(
            'start', default='1970-01-01 12:00:00', type=str)
        now = datetime.datetime.fromtimestamp(
            time.time()).strftime('%Y-%m-%d %H:%M:%S')
        end = request.args.get('end', default=now, type=str)

        if(end !=now):
            end += " 23:59:59"

        if(start == end):
            start +=" 00:00:00"
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


@app.route('/user', methods=['GET', 'POST'])
def user():

    if request.method == "GET":
        paramslist = list(request.args.to_dict().keys())
        if 'user' in paramslist:
            paramslist.remove('user')
        if 'name' in paramslist:
            paramslist.remove('name')
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        else:
            user = request.args.get('user', default=None, type=str)
            name = request.args.get('name', default=None, type=str)
            return get_users(user, name)

    if request.method == "POST":
        # should be no params all info should be in the body
        paramslist = list(request.args.to_dict().keys())
        if(paramslist):
            return jsonify(error="400 Bad Request Unkown Parameters: \'{}\'".format('\', \''.join(paramslist))), status.HTTP_400_BAD_REQUEST
        else:
            return create_user()


if __name__ == '__main__':
    app.run(debug=True)
