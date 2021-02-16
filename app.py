from flask import Flask, render_template, request
from flask_mysqldb import MySQL
from flask_api import status
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


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/weights', methods=['GET','POST'])
def weights():
    if request.method == "GET":
        
        #Connect to DB and get all the info from weights table
        #return json
        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights;")
        data = cur.fetchall()
        cur.close()
        return json.dumps(data),status.HTTP_200_OK

    if request.method == "POST":
        
        #Check if request has json and has the two required fields
        if not request.json or not 'user' in request.json or not 'weight' in request.json:
            return "",status.HTTP_400_BAD_REQUEST

        #extract content + make timestamp
        content = request.json
        user = content['user']
        weight = content['weight']
        ts = time.time()
        timestamp = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        #add the generated timestamp used for response
        content['timestamp'] = timestamp 

        cur = mysql.connection.cursor()

        try:
            cur.execute("INSERT INTO `weightlossgrapher`.`weights` (`user_id`,`timestamp`,`weight`) VALUES (%s,%s,%s);",(user,timestamp,weight))
            mysql.connection.commit()
        except:
            mysql.connection.rollback()
            return "",status.HTTP_400_BAD_REQUEST

        cur.close()
        return json.dumps(content),status.HTTP_201_CREATED


if __name__ == '__main__':
    app.run(debug=True)