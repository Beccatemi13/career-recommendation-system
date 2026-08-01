from werkzeug.security import generate_password_hash
import mysql.connector

print("Starting script...")

try:
    conn = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Intelligence_1",
    database="career_recommendation_system",
    connection_timeout=5
)

    print("Connected to MySQL!")

    cursor = conn.cursor()

    username = "admin"
    hashed_password = generate_password_hash("admin123")

    cursor.execute("""
        INSERT INTO admins (username, password)
        VALUES (%s, %s)
    """, (username, hashed_password))

    conn.commit()

    print("✅ Admin account created successfully!")

    cursor.close()
    conn.close()

except Exception as e:
    print("❌ ERROR:")
    print(e)