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


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/weights', methods=['GET','POST'])
def weights():
    if request.method == "GET":
        
        user = request.args.get('user',default=None,type=str)
        cur = mysql.connection.cursor()

        if(user==None):
            try:
                cur.execute("SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights")
            except:
                return jsonify(error="500 Internal Server Error"),status.HTTP_500_INTERNAL_SERVER_ERROR

        else:
            try:
                cur.execute("SELECT user_id,CAST(timestamp AS CHAR(30)),weight FROM weightlossgrapher.weights WHERE user_id = %s;",user)
            except:
                return jsonify(error= "404 User Not Found"),status.HTTP_404_NOT_FOUND

        fields = [i[0] for i in cur.description]
        fields[1] = 'timestamp'
        results = [dict(zip(fields,row))   for row in cur.fetchall()]

        cur.close()
        return json.dumps(results),status.HTTP_200_OK

    if request.method == "POST":
        
        #Check if request has json and has the two required fields
        if not request.json or not 'user' in request.json or not 'weight' in request.json:
            return jsonify(),status.HTTP_400_BAD_REQUEST

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