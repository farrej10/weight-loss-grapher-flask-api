# Weight-Loss Flask API

This API will allow my [weight-loss website](https://github.com/farrej10/weight-loss-web-ui) to get data from a MySQL database.
It provides a simple RESTful api to interface with.

## Install (Dev)

Create a new virtual environment.
    
    python -m venv flaskvenv

Install the required packages.
    
    pip install -r requirements.txt

Make a `.env` file that will holds the following details about your MySQL instance.
    
    MYSQL_HOST = 'hostname/IP'
    MYSQL_USER = 'user'
    MYSQL_PASSWORD = 'pass'
    MYSQL_DB = 'dbscheme'

## Run the app

    python app.py

Or

    flask run

# REST API

The REST API usage is described below.

## Get list of users

### Request

`GET /user`

    curl http://localhost:5000/user

### Response

 
    HTTP 1.0, assume close after body
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 2
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 16:47:08 GMT

    []

## Create a new user

### Request

`POST /user`

    curl --header "Content-Type: application/json" \
      --request POST \
      --data '{"name":"James"}' \
      http://localhost:5000/user

### Response

    HTTP 1.1, assume close after body
    HTTP/1.1 201 CREATED
    Content-Type: application/json
    Content-Length: 47
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 16:50:43 GMT
    
    [
      {
        "id": 26, 
        "name": "James"
      }
    ]

## Get a specific user by id

### Request

`GET /user?id=1`

    curl http://localhost:5000/user?id=1

### Response

    HTTP 1.1, assume close after body
    HTTP/1.1 200 OK
    Content-Type: application/json
    Content-Length: 45
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 17:37:10 GMT

    [
      {
        "id": 1, 
        "name": "test"
      }
    ]


## Get a non-existent user

### Request

`GET /user?id=123`

    curl -v http://localhost:5000/user?id=123

### Response

    HTTP 1.0, assume close after body
    HTTP/1.0 404 NOT FOUND
    Content-Type: application/json
    Content-Length: 27
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 17:38:51 GMT

    {
      "error": "Not Found"
    }

## Get a specific user by name

Returns a list of users with that name

### Request

`GET /user?name=james`

    curl http://localhost:5000/user?name=james

### Response

    HTTP 1.0, assume close after body
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 181
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 17:41:31 GMT

    [
      {
        "id": 4, 
        "name": "james"
      }, 
      {
        "id": 25, 
        "name": "James"
      }, 
      {
        "id": 26, 
        "name": "James"
      }, 
      {
        "id": 27, 
        "name": "James"
      }
    ]


## Get a list of weights

Returns a list of all the weight data for all users

### Request

`GET /weights`

    curl http://localhost:5000/weights

### Response

    HTTP 1.0, assume close after body
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 4813
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 18:26:09 GMT

    [
      {
        "timestamp": "2021-02-12 21:57:10", 
        "user_id": 1, 
        "weight": 55.0
      }, 
      {
        "timestamp": "2021-02-14 23:12:31", 
        "user_id": 2, 
        "weight": 51.0
      }, 
      {
        "timestamp": "2021-02-15 00:59:20", 
        "user_id": 3, 
        "weight": 66.0
      }, 
      {
        "timestamp": "2021-02-15 01:00:34", 
        "user_id": 1, 
        "weight": 66.0
      } 
    ]

## Get a list of weights filtered by user

Returns a list of all the weight data for a specific user

### Request

`GET /weights?user=1`

    curl http://localhost:5000/weights?user=1

### Response

    HTTP 1.0, assume close after body
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 4007
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 18:31:39 GMT

    [
      {
        "timestamp": "2021-02-12 21:46:09", 
        "user_id": 1, 
        "weight": 55.0
      }, 
      {
        "timestamp": "2021-02-12 21:57:10", 
        "user_id": 1, 
        "weight": 55.0
      }, 
      {
        "timestamp": "2021-02-14 23:12:31", 
        "user_id": 1, 
        "weight": 51.0
      }, 
      {
        "timestamp": "2021-02-15 00:59:20", 
        "user_id": 1, 
        "weight": 66.0
      }
    ]

## Get a list of weights filtered by name

Returns a list of all the weight data for all users with a specific name

### Request

`GET /weights?name=test`

    curl http://localhost:5000/weights?name=test

### Response

    HTTP 1.0, assume close after body
    HTTP/1.0 200 OK
    Content-Type: application/json
    Content-Length: 5402
    Server: Werkzeug/1.0.1 Python/3.9.1
    Date: Sat, 20 Feb 2021 18:35:29 GMT
    
    [
      {
        "name": "test", 
        "timestamp": "2021-02-19 21:43:25", 
        "user_id": 1, 
        "weight": 81.5
      }, 
      {
        "name": "test", 
        "timestamp": "2021-02-20 00:49:46", 
        "user_id": 2, 
        "weight": 81.5
      }, 
      {
        "name": "test", 
        "timestamp": "2021-02-20 17:34:27", 
        "user_id": 1, 
        "weight": 82.5
      }
    ]

## Additional Filter Parameters

There are additional paramters that can be used to narrow down the selection:

- The `start` parameter allows filtering from that date to the current date.

- The `end` parameter allows filtering from the start of time till that date.

- Both can be used together to get a range between `start` to `end` dates.

- If `start` and `end` are equal, the results will be all the weights on that date.

A note on dates, they must be in the numeric form `year-month-day` e.g. `2020-5-25`

### Example Requests

Get user `1`'s weights from `2020-05-02` till present

`GET /weights?user=1&start=2020-05-02`

Get user `1`'s weights from the start of time until `2020-05-02`

`GET /weights?user=1&end=2020-05-02`

Get user `1`'s weight between `2020-05-02` and `2020-07-02`

`GET /weights?user=1&start=2020-05-02&end=2020-07-02`

