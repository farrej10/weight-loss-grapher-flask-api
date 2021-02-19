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


def get_weigths():  # Return weights table

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights")
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
        return jsonify(error="Internal Server Error"), status.HTTP_500_INTERNAL_SERVER_ERROR


def get_weights_by_user(user,start,end):  # Return all weights for a user

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s AND timestamp BETWEEN  %s AND %s;", (user,start,end))
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
        return jsonify(error="User Not Found or No Weight Data with that User"), status.HTTP_404_NOT_FOUND


def get_weights_by_name(name,start,end):  # return all weights for a user's name

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id, name, timestamp, weight FROM user t1 INNER JOIN weights t2 ON t1.id = t2.user_id WHERE name = %s AND timestamp BETWEEN  %s AND %s;", (name,start,end))
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
        return jsonify(error="Name Not Found or No Weight Data with that Name"), status.HTTP_404_NOT_FOUND


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


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/weights', methods=['GET', 'POST'])
def weights():
    if request.method == "GET":

        user = request.args.get('user', default=None, type=str)
        name = request.args.get('name', default=None, type=str)
        start = request.args.get('start',default='1970-01-01 12:00:00', type=str)
        end = request.args.get('end',default=datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'),type=str)
        
        
        if(start==end):
            start=start+" 00:00:00"
            end=end+ " 23:59:59"
            #return jsonify(error="Bad Request"),status.HTTP_400_BAD_REQUEST
        # user is unique therfore select based on that
        if (user != None):
            return get_weights_by_user(user,start,end)
        if (name != None):
            return get_weights_by_name(name,start,end)
        else:
            return get_weigths()

    if request.method == "POST":
        return create_weight_for_user(request)


if __name__ == '__main__':
    app.run(debug=True)
