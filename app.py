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


def get_all_weights():  # Return weights table

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


def get_user_weights(user):  # Return all weights for a user

    cur = mysql.connection.cursor()
    try:
        cur.execute(
            "SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s;", (user,))
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
        return jsonify(error="User Not Found"), status.HTTP_404_NOT_FOUND


def create_user_weight(request):  # Create a weight entry for a user

    # Check if request has json and has the two required fields
    if not request.json or not 'user' in request.json or not 'weight' in request.json:
        return jsonify(error="400 Bad Request"), status.HTTP_400_BAD_REQUEST

    # extract content + make timestamp
    content = request.json
    user = content['user']
    weight = content['weight']
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
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
        cur = mysql.connection.cursor()

        if(user == None):
            return get_all_weights()

        else:
            return get_user_weights(user)

    if request.method == "POST":
        return create_user_weight(request)

if __name__ == '__main__':
    app.run(debug=True)
