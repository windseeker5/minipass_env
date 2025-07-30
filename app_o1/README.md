# dpm
Digital Pass Manager system ( python, flask )


## How to setup after git clone...
$ cd dpm

$ python -m venv venv

$ cd backend

$ pip install -r requirements.txt


# How to

### Step 1: Delete Existing Migrations and Database
rm -rf migrations

rm database.db  # Delete SQLite database (if using SQLite)

### Step 2: Initialize Migrations Again
flask db init

flask db migrate -m "Initial migration"

flask db upgrade


### Web Interface 
http://127.0.0.1:5000

