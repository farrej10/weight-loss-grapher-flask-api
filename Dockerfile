#Use the Python3.7.2 image
FROM python:3.7.2-stretch

# Set the working directory to /app
WORKDIR /app

#for better build caching
ADD requirements.txt /app

# Install the dependencies
RUN apt-get update
RUN apt-get install -y default-libmysqlclient-dev
RUN apt-get install -y build-essential

RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app 
ADD . /app

# run the command to start uWSGI
CMD ["uwsgi", "app.ini"]