import os

MYSQL_HOST = os.environ.get("MYSQLHOST")
MYSQL_USER = os.environ.get("MYSQLUSER")
MYSQL_PASSWORD = os.environ.get("MYSQLPASSWORD")
MYSQL_DB = os.environ.get("MYSQLDATABASE")
MYSQL_PORT = int(os.environ.get("MYSQLPORT", 3306))

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "career_recommendation_secret_key"
)

CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET")