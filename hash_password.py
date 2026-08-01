from werkzeug.security import generate_password_hash

password = "admin123"

print(generate_password_hash(password))