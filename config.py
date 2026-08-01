import os

MYSQL_HOST = os.environ.get("MYSQLHOST")
MYSQL_USER = os.environ.get("MYSQLUSER")
MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD")
MYSQL_DB = os.environ.get("MYSQLDATABASE")

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "career_recommendation_secret_key"
)