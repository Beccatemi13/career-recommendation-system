# ============================================================
# CAREER RECOMMENDATION SYSTEM
# Final Year Project
# Developed with Flask + MySQL
# ============================================================

# ============================================================
# IMPORTS
# ============================================================

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    make_response,
    send_file
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from werkzeug.utils import secure_filename

import os
import tempfile
from io import BytesIO
from datetime import datetime

import config

# ============================================================
# MySQLdb)
# ============================================================

from flask_mysqldb import MySQL
from MySQLdb.cursors import DictCursor

# ============================================================
# PDF
# ============================================================

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor

# ============================================================
# CLOUDINARY
# ============================================================

import cloudinary
import cloudinary.uploader

# ============================================================
# FLASK CONFIGURATION
# ============================================================

app = Flask(__name__)

cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True
)

app.secret_key = config.SECRET_KEY

# ============================================================
# MYSQL CONFIGURATION
# ============================================================

app.config["MYSQL_HOST"] = config.MYSQL_HOST
app.config["MYSQL_USER"] = config.MYSQL_USER
app.config["MYSQL_PASSWORD"] = config.MYSQL_PASSWORD
app.config["MYSQL_DB"] = config.MYSQL_DB
app.config["MYSQL_PORT"] = config.MYSQL_PORT

mysql = MySQL(app)

# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")

# ============================================================
# REGISTER
# ============================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = request.form["password"]
        department = request.form["department"]
        level = request.form["level"]

        cursor = mysql.connection.cursor()

        cursor.execute(

            "SELECT id FROM students WHERE email=%s",

            (email,)

        )

        if cursor.fetchone():

            flash("Email already exists.", "danger")

            cursor.close()

            return redirect(url_for("register"))

        hashed_password = generate_password_hash(password)

        cursor.execute("""

        INSERT INTO students(

        full_name,
        email,
        password,
        department,
        level

        )

        VALUES(

        %s,%s,%s,%s,%s

        )

        """,(

        full_name,
        email,
        hashed_password,
        department,
        level

        ))

        mysql.connection.commit()

        cursor.close()

        flash("Registration successful. Please login.","success")

        return redirect(url_for("login"))

    return render_template("register.html")

# ============================================================
# LOGIN
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()

        cursor.execute("""

        SELECT

        id,
        full_name,
        email,
        password,
        department,
        level,
        profile_picture

        FROM students

        WHERE email=%s

        """,(email,))

        user = cursor.fetchone()

        cursor.close()

        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["full_name"] = user[1]
            session["email"] = user[2]
            session["department"] = user[4]
            session["level"] = user[5]
            session["profile_picture"] = user[6] if user[6] else "default.png"
            session["theme"] = "light"

            flash("Login successful.","success")
            
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.","danger")

    return render_template("login.html")

# ============================================================
# STUDENT FORGOT PASSWORD
# ============================================================

@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:

            flash("Passwords do not match.", "danger")
            return redirect(url_for("forgot_password"))

        cursor = mysql.connection.cursor()

        cursor.execute(

            "SELECT id FROM students WHERE email=%s",

            (email,)

        )

        user = cursor.fetchone()

        if not user:

            cursor.close()

            flash("Email not found.", "danger")

            return redirect(url_for("forgot_password"))

        hashed_password = generate_password_hash(new_password)

        cursor.execute(

            "UPDATE students SET password=%s WHERE email=%s",

            (hashed_password, email)

        )

        mysql.connection.commit()

        cursor.close()

        flash("Password updated successfully. Please login.", "success")

        return redirect(url_for("login"))

    return render_template("forgot_password.html")

# ============================================================
# STUDENT CHANGE PASSWORD
# ============================================================

@app.route("/change_password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(DictCursor)

    if request.method == "POST":

        current_password = request.form["current_password"]

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]

        cursor.execute("""

            SELECT password

            FROM students

            WHERE id=%s

        """, (session["user_id"],))

        student = cursor.fetchone()

        if not check_password_hash(
            student["password"],
            current_password
        ):

            cursor.close()

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return redirect(
                url_for("change_password")
            )

        if new_password != confirm_password:

            cursor.close()

            flash(
                "New passwords do not match.",
                "warning"
            )

            return redirect(
                url_for("change_password")
            )

        hashed_password = generate_password_hash(
            new_password
        )

        cursor.execute("""

            UPDATE students

            SET password=%s

            WHERE id=%s

        """, (

            hashed_password,

            session["user_id"]

        ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Password changed successfully.",

            "success"

        )

        return redirect(
            url_for("settings")
        )

    cursor.close()

    return render_template(
        "change_password.html"
    )

# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("login"))

# ============================================================
# SETTINGS
# ============================================================
@app.route("/settings")
def settings():

    if "user_id" not in session:

        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    return render_template("settings.html")

# ============================================================
# ADMIN SETTINGS
# ============================================================

@app.route("/admin/settings")
def admin_settings():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    return render_template("admin_settings.html")

# ============================================================
# STUDENT SUPPORT REQUESTS
# ============================================================

@app.route("/support_requests")
def support_requests():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    # Mark all resolved replies as read
    cursor.execute("""

        UPDATE support_requests

        SET is_read = 1

        WHERE

            student_id = %s

            AND status = 'Resolved'

            AND is_read = 0

    """,

    (

        session["user_id"],

    ))

    mysql.connection.commit()

    # Fetch all support requests
    cursor.execute("""

        SELECT

            id,
            subject,
            message,
            admin_reply,
            status,
            created_at,
            resolved_at

        FROM support_requests

        WHERE student_id=%s

        ORDER BY created_at DESC

    """,

    (

        session["user_id"],

    ))

    requests = cursor.fetchall()

    cursor.close()

    return render_template(

        "support_requests.html",

        requests=requests

    )

# ============================================================
# ADMIN SUPPORT REQUESTS
# ============================================================

@app.route("/admin/support_requests")
def admin_support_requests():

    if "admin_id" not in session:

        flash(

            "Please login first.",

            "warning"

        )

        return redirect(

            url_for("admin_login")

        )

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            support_requests.id,

            students.full_name,

            students.email,

            support_requests.subject,

            support_requests.message,

            support_requests.status,

            support_requests.created_at

        FROM support_requests

        JOIN students

        ON support_requests.student_id = students.id

        ORDER BY support_requests.created_at DESC

    """)

    requests = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_support_requests.html",

        requests=requests

    )

# ============================================================
# ADMIN SUPPORT REQUESTS RESOLVE
# ============================================================
@app.route("/admin/support_requests/resolve/<int:id>")
def resolve_support_request(id):

    if "admin_id" not in session:

        return redirect(

            url_for("admin_login")

        )

    cursor = mysql.connection.cursor()

    cursor.execute("""

        UPDATE support_requests

        SET status='Resolved'

        WHERE id=%s

    """,

    (

        id,

    ))

    mysql.connection.commit()

    cursor.close()

    flash(

        "Request marked as resolved.",

        "success"

    )

    return redirect(

        url_for("admin_support_requests")

    )
# ============================================================
# TOGGLE DARK/LIGHT THEME
# ============================================================

from flask import request

@app.route("/toggle_theme")
def toggle_theme():

    if session.get("theme") == "dark":

        session["theme"] = "light"

        flash(
            "Light mode enabled.",
            "success"
        )

    else:

        session["theme"] = "dark"

        flash(
            "Dark mode enabled.",
            "success"
        )

    if request.referrer:

        return redirect(request.referrer)

    if "admin_id" in session:

        return redirect(url_for("admin_dashboard"))

    return redirect(url_for("dashboard"))

# ============================================================
# FILE UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def login_required():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return False

    return True

# ============================================================
# ADMIN LOGIN
# ============================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        cursor = mysql.connection.cursor()

        cursor.execute("""
            SELECT *
    FROM admins
    WHERE username=%s
        """, (username,))

        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin[2], password):

            session["admin_id"] = admin[0]
            session["admin_username"] = admin[1]

            flash("Welcome Administrator!", "success")

            return redirect(url_for("admin_dashboard"))

        flash("Invalid username or password.", "danger")

    return render_template("admin_login.html")

# ============================================================
# ADMIN FORGOT PASSWORD
# ============================================================

@app.route("/admin/forgot_password", methods=["GET", "POST"])
def admin_forgot_password():

    if request.method == "POST":

        username = request.form["username"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:

            flash("Passwords do not match.", "danger")

            return redirect(url_for("admin_forgot_password"))

        cursor = mysql.connection.cursor()

        cursor.execute(

            "SELECT id FROM admins WHERE username=%s",

            (username,)

        )

        admin = cursor.fetchone()

        if not admin:

            cursor.close()

            flash("Username not found.", "danger")

            return redirect(url_for("admin_forgot_password"))

        hashed_password = generate_password_hash(new_password)

        cursor.execute(

            "UPDATE admins SET password=%s WHERE username=%s",

            (hashed_password, username)

        )

        mysql.connection.commit()

        cursor.close()

        flash("Password updated successfully. Please login.", "success")

        return redirect(url_for("admin_login"))

    return render_template("admin_forgot_password.html")

# ============================================================
# ADMIN CHANGE PASSWORD
# ============================================================

@app.route("/admin/change_password", methods=["GET", "POST"])
def admin_change_password():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    if request.method == "POST":

        current_password = request.form["current_password"]

        new_password = request.form["new_password"]

        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:

            flash("New passwords do not match.", "danger")

            return redirect(url_for("admin_change_password"))

        cursor = mysql.connection.cursor()

        cursor.execute("""

            SELECT password

            FROM admins

            WHERE id=%s

        """, (session["admin_id"],))

        admin = cursor.fetchone()

        if not admin:

            cursor.close()

            flash("Administrator not found.", "danger")

            return redirect(url_for("admin_login"))

        if not check_password_hash(admin[0], current_password):

            cursor.close()

            flash("Current password is incorrect.", "danger")

            return redirect(url_for("admin_change_password"))

        hashed_password = generate_password_hash(new_password)

        cursor.execute("""

            UPDATE admins

            SET password=%s

            WHERE id=%s

        """, (

            hashed_password,

            session["admin_id"]

        ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Password changed successfully.",

            "success"

        )

        return redirect(

            url_for("admin_dashboard")

        )

    return render_template(

        "admin_change_password.html"

    )

# ============================================================
# ADMIN LOGOUT
# ============================================================
@app.route("/admin/logout")
def admin_logout():

    session.clear()

    flash("Logged out successfully.", "success")

    return redirect(url_for("admin_login"))

# ============================================================
# ADMIN DASHBOARD
# ============================================================

@app.route("/admin/dashboard")
def admin_dashboard():
    
    if "admin_id" not in session:

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    # --------------------------------------------------------
    # SUMMARY COUNTS
    # --------------------------------------------------------

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM careers")
    total_careers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM assessment")
    total_assessments = cursor.fetchone()[0]

    total_recommendations = total_assessments

    # --------------------------------------------------------
    # CAREER RECOMMENDATION CHART
    # --------------------------------------------------------

    cursor.execute("""

        SELECT

            recommendation,

            COUNT(*) AS total

        FROM assessment

        WHERE recommendation IS NOT NULL

        GROUP BY recommendation

        ORDER BY total DESC

    """)

    career_chart = cursor.fetchall()

    # --------------------------------------------------------
    # SUPPORT REQUEST STATUS CHART
    # --------------------------------------------------------

    cursor.execute("""

        SELECT

            COUNT(*)

        FROM support_requests

        WHERE status='Pending'

    """)

    pending_requests = cursor.fetchone()[0]

    cursor.execute("""

        SELECT

            COUNT(*)

        FROM support_requests

        WHERE status='Resolved'

    """)

    resolved_requests = cursor.fetchone()[0]

    # --------------------------------------------------------
    # RECENT REGISTERED STUDENTS
    # --------------------------------------------------------

    cursor.execute("""

        SELECT

            full_name,
            email,
            department,
            level,
            created_at

        FROM students

        ORDER BY created_at DESC

        LIMIT 5

    """)

    latest_students = cursor.fetchall()

    # --------------------------------------------------------
    # RECENT ASSESSMENTS
    # --------------------------------------------------------

    cursor.execute("""

        SELECT

            students.full_name,
            assessment.top_career,
            assessment.overall_score,
            assessment.assessment_date

        FROM assessment

        JOIN students

        ON assessment.student_id = students.id

        ORDER BY assessment.assessment_date DESC

        LIMIT 5

    """)

    recent_assessments = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_dashboard.html",

        total_students=total_students,

        total_careers=total_careers,

        total_assessments=total_assessments,

        total_recommendations=total_recommendations,

        career_chart=career_chart,

        pending_requests=pending_requests,

        resolved_requests=resolved_requests,

        latest_students=latest_students,

        recent_assessments=recent_assessments

    )

  
# ============================================================
# ADMIN PROFILE
# ============================================================

@app.route("/admin/profile")
def admin_profile():

    if "admin_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            full_name,
            email,
            profile_picture
        FROM admins
        WHERE id=%s
    """, (session["admin_id"],))

    admin = cursor.fetchone()

    cursor.close()

    return render_template(
        "admin_profile.html",
        admin=admin
    )
# ============================================================
# ADMIN - ADD CAREER
# ============================================================

@app.route("/admin/add_career", methods=["GET", "POST"])
def admin_add_career():

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        cursor = mysql.connection.cursor()

        cursor.execute("""

        INSERT INTO careers
        (
            career_name,
            description,
            programming,
            mathematics,
            communication,
            leadership,
            creativity,
            problem_solving,
            teamwork,
            technology_interest,
            business_interest,
            healthcare_interest,
            analytical_thinking,
            research_interest,
            public_speaking,
            entrepreneurship,
            attention_to_detail,
            certifications,
            learning_platforms,
            skills_to_improve,
            related_careers,
            salary_range,
            career_outlook
        )

        VALUES
        (
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s
        )

        """,

        (

            request.form["career_name"],
            request.form["description"],
            request.form["programming"],
            request.form["mathematics"],
            request.form["communication"],
            request.form["leadership"],
            request.form["creativity"],
            request.form["problem_solving"],
            request.form["teamwork"],
            request.form["technology_interest"],
            request.form["business_interest"],
            request.form["healthcare_interest"],
            request.form["analytical_thinking"],
            request.form["research_interest"],
            request.form["public_speaking"],
            request.form["entrepreneurship"],
            request.form["attention_to_detail"],
            request.form["certifications"],
            request.form["learning_platforms"],
            request.form["skills_to_improve"],
            request.form["related_careers"],
            request.form["salary_range"],
            request.form["career_outlook"]

        ))

        mysql.connection.commit()

        cursor.close()

        flash("Career added successfully!", "success")

        return redirect(url_for("admin_manage_careers"))

    return render_template("admin_add_careers.html")

# ==========================================================
# ADMIN MANAGE CAREERS
# ==========================================================

@app.route("/admin/manage_careers")
def admin_manage_careers():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    search = request.args.get("search", "").strip()

    cursor = mysql.connection.cursor()

    if search:

        cursor.execute("""

            SELECT *

            FROM careers

            WHERE

                career_name LIKE %s

                OR career_field LIKE %s

                OR description LIKE %s

                OR required_skills LIKE %s

                OR certifications LIKE %s

                OR learning_platforms LIKE %s

                OR industries LIKE %s

                OR career_outlook LIKE %s

            ORDER BY career_name ASC

        """,

        (

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%",

            "%" + search + "%"

        ))
    else:

        cursor.execute("""

            SELECT *

            FROM careers

            ORDER BY career_name ASC

        """)

    careers = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_manage_careers.html",

        careers=careers,

        search=search

    )

# ============================================================
# ADMIN - EDIT CAREER
# ============================================================

@app.route("/admin/edit_career/<int:career_id>", methods=["GET", "POST"])
def admin_edit_career(career_id):

    if "admin_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    if request.method == "POST":

        cursor.execute("""

        UPDATE careers SET

            career_name=%s,
            career_field=%s,
            description=%s,
            why_fits=%s,
            daily_responsibilities=%s,
            required_skills=%s,
            recommended_personality=%s,
            activities_to_improve=%s,
            certifications=%s,
            learning_platforms=%s,
            workplaces=%s,
            industries=%s,
            career_outlook=%s,
            minimum_qualification=%s,
            average_study_years=%s,
            salary_note=%s,
            did_you_know=%s

        WHERE id=%s

        """, (

            request.form["career_name"],
            request.form["career_field"],
            request.form["description"],
            request.form.get("why_fits"),
            request.form.get("daily_responsibilities"),
            request.form.get("required_skills"),
            request.form.get("recommended_personality"),
            request.form.get("activities_to_improve"),
            request.form.get("certifications"),
            request.form.get("learning_platforms"),
            request.form.get("workplaces"),
            request.form.get("industries"),
            request.form.get("career_outlook"),
            request.form.get("minimum_qualification"),
            request.form.get("average_study_years"),
            request.form.get("salary_note"),
            request.form.get("did_you_know"),
            career_id

        ))

        mysql.connection.commit()

        flash("Career updated successfully!", "success")

        return redirect(url_for("admin_manage_careers"))

    cursor.execute(
        "SELECT * FROM careers WHERE id=%s",
        (career_id,)
    )

    career = cursor.fetchone()

    cursor.close()

    return render_template(
        "admin_edit_career.html",
        career=career
    )

# ============================================================
# ADMIN VIEW STUDENT
# ============================================================

@app.route("/admin/student/<int:student_id>")
def admin_view_student(student_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")
        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT
            id,
            full_name,
            email,
            gender,
            date_of_birth,
            department,
            level,
            profile_picture

        FROM students

        WHERE id=%s

    """, (student_id,))

    student = cursor.fetchone()

    cursor.close()

    if not student:

        flash("Student not found.", "danger")
        return redirect(url_for("admin_students"))

    return render_template(
        "admin_view_student.html",
        student=student
    )

# ============================================================
# ADMIN EDIT STUDENT
# ============================================================
@app.route("/admin/student/edit/<int:student_id>", methods=["GET", "POST"])
def admin_edit_student(student_id):

    if "admin_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("admin_login"))

   
    cursor = mysql.connection.cursor(DictCursor)

    if request.method == "POST":

        full_name = request.form["full_name"]
        department = request.form["department"]
        level = request.form["level"]
        gender = request.form["gender"]
        date_of_birth = request.form["date_of_birth"]

        cursor.execute("""
            UPDATE students
            SET
                full_name=%s,
                department=%s,
                level=%s,
                gender=%s,
                date_of_birth=%s
            WHERE id=%s
        """,
        (
            full_name,
            department,
            level,
            gender,
            date_of_birth,
            student_id
        ))

        mysql.connection.commit()

        cursor.close()

        flash("Student updated successfully.", "success")

        return redirect(url_for("admin_students"))

    cursor.execute("""
        SELECT *
        FROM students
        WHERE id=%s
    """,(student_id,))

    student = cursor.fetchone()

    cursor.close()

    return render_template(
        "admin_edit_student.html",
        student=student
    )

# ============================================================
# ADMIN DELETE STUDENT
# ============================================================

@app.route("/admin/student/delete/<int:student_id>")
def admin_delete_student(student_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    cursor.execute(
    "DELETE FROM assessment WHERE student_id=%s",
    (student_id,)
)

    cursor.execute(
    "DELETE FROM students WHERE id=%s",
    (student_id,)
)
    
    mysql.connection.commit()

    cursor.close()

    flash(

        "Student deleted successfully.",

        "success"

    )

    return redirect(url_for("admin_students"))

# ============================================================
# ADMIN VIEW SUPPORT REQUEST
# ============================================================

@app.route(
    "/admin/support/<int:request_id>",
    methods=["GET", "POST"]
)
def admin_view_support(request_id):

    if "admin_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("admin_login")
        )

    cursor = mysql.connection.cursor(DictCursor)

    # ========================================================
    # SAVE REPLY / RESOLVE REQUEST
    # ========================================================

    if request.method == "POST":

        admin_reply = request.form["admin_reply"]

        action = request.form["action"]

        # -----------------------------
        # SAVE REPLY ONLY
        # -----------------------------

        if action == "save":

            cursor.execute("""

                UPDATE support_requests

                SET

                    admin_reply = %s

                WHERE id = %s

            """,

            (

                admin_reply,

                request_id

            ))

            mysql.connection.commit()

            flash(

                "Reply saved successfully.",

                "success"

            )

        # -----------------------------
        # RESOLVE REQUEST
        # -----------------------------

        elif action == "resolve":

            cursor.execute("""

                UPDATE support_requests

                SET

                    admin_reply = %s,

                    status = 'Resolved',

                    resolved_at = NOW(),

                    is_read = 0

                WHERE id = %s

            """,

            (

                admin_reply,

                request_id

            ))

            mysql.connection.commit()

            flash(

                "Request resolved successfully.",

                "success"

            )

        return redirect(

            url_for(

                "admin_view_support",

                request_id=request_id

            )

        )

    # ========================================================
    # LOAD SUPPORT REQUEST
    # ========================================================

    cursor.execute("""

        SELECT

            sr.id,

            sr.subject,

            sr.message,

            sr.admin_reply,

            sr.status,

            sr.created_at,

            sr.resolved_at,

            s.id AS student_id,

            s.full_name,

            s.email,

            s.department,

            s.level

        FROM support_requests sr

        JOIN students s

            ON sr.student_id = s.id

        WHERE sr.id = %s

    """,

    (

        request_id,

    ))

    support_request = cursor.fetchone()

    cursor.close()

    # ========================================================
    # REQUEST NOT FOUND
    # ========================================================

    if not support_request:

        flash(

            "Support request not found.",

            "danger"

        )

        return redirect(

            url_for("admin_support_requests")

        )

    # ========================================================
    # DISPLAY PAGE
    # ========================================================

    return render_template(

    "admin_view_support.html",

    support_request=support_request

)

# ============================================================
# ADMIN RESOLVE SUPPORT
# ============================================================

@app.route("/admin/resolve_support/<int:request_id>")
def admin_resolve_support(request_id):

    if "admin_id" not in session:
        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""

    UPDATE support_requests

    SET

    status='Resolved',

    resolved_at=NOW()

    WHERE id=%s

    """, (request_id,))

    mysql.connection.commit()

    cursor.close()

    flash("Support request resolved successfully.", "success")

    return redirect(url_for("admin_support_requests"))

# ============================================================
# ADMIN ASSESSMENTS
# ============================================================

@app.route("/admin/assessments")
def admin_assessments():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            assessment.*,

            students.full_name

        FROM assessment

        JOIN students

        ON assessment.student_id = students.id

        ORDER BY assessment.assessment_date DESC

    """)

    assessments = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_assessments.html",

        assessments=assessments

    )

# ============================================================
# ADMIN VIEW ASSESSMENT
# ============================================================

@app.route("/admin/assessment/<int:assessment_id>")
def admin_view_assessment(assessment_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            assessment.*,

            students.full_name,

            students.email,

            students.department,

            students.level

        FROM assessment

        JOIN students

        ON assessment.student_id = students.id

        WHERE assessment.id=%s

    """, (assessment_id,))

    assessment = cursor.fetchone()

    cursor.close()

    if not assessment:

        flash("Assessment not found.", "danger")

        return redirect(url_for("admin_assessments"))

    return render_template(

        "admin_view_assessment.html",

        assessment=assessment

    )


# ============================================================
# ADMIN DELETE ASSESSMENT
# ============================================================

@app.route("/admin/assessment/delete/<int:assessment_id>")
def admin_delete_assessment(assessment_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    cursor.execute(

        "DELETE FROM assessment WHERE id=%s",

        (assessment_id,)

    )

    mysql.connection.commit()

    cursor.close()

    flash(

        "Assessment deleted successfully.",

        "success"

    )

    return redirect(url_for("admin_assessments"))

# ============================================================
# ADMIN STUDENTS
# ============================================================

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            id,
            full_name,
            email,
            gender,
            department,
            level

        FROM students

        ORDER BY full_name ASC

    """)

    students = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_students.html",

        students=students

    )

# ============================================================
# ADMIN RECOMMENDATIONS
# ============================================================

@app.route("/admin/recommendations")
def admin_recommendations():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            assessment.id,
            assessment.student_id,
            assessment.overall_score,
            assessment.top_career,
            assessment.recommendation,
            assessment.assessment_date,

            students.full_name,
            students.department,
            students.level

        FROM assessment

        JOIN students

        ON students.id = assessment.student_id

        WHERE assessment.top_career IS NOT NULL

        ORDER BY assessment.assessment_date DESC

    """)

    recommendations = cursor.fetchall()

    cursor.close()

    return render_template(

        "admin_recommendations.html",

        recommendations=recommendations

    )

# ============================================================
# ADMIN VIEW RECOMMENDATION
# ============================================================

@app.route("/admin/recommendation/<int:assessment_id>")
def admin_view_recommendation(assessment_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

        SELECT

            assessment.*,

            students.full_name,

            students.email,

            students.department,

            students.level

        FROM assessment

        JOIN students

        ON students.id = assessment.student_id

        WHERE assessment.id=%s

    """, (assessment_id,))

    recommendation = cursor.fetchone()

    cursor.close()

    if not recommendation:

        flash("Recommendation not found.", "danger")

        return redirect(url_for("admin_recommendations"))

    return render_template(

        "admin_view_recommendation.html",

        recommendation=recommendation

    )

# ============================================================
# ADMIN DELETE RECOMMENDATION
# ============================================================

@app.route("/admin/recommendation/delete/<int:assessment_id>")
def admin_delete_recommendation(assessment_id):

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    cursor.execute(

        """

        UPDATE assessment

        SET

            overall_score=0,

            top_career=NULL,

            recommendation=NULL

        WHERE id=%s

        """,

        (assessment_id,)

    )

    mysql.connection.commit()

    cursor.close()

    flash(

        "Recommendation removed successfully.",

        "success"

    )

    return redirect(url_for("admin_recommendations"))

# ============================================================
# ADMIN ANALYTICS
# ============================================================

@app.route("/admin/analytics")
def admin_analytics():

    if "admin_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("admin_login"))

    cursor = mysql.connection.cursor()

    # Total Students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Total Careers
    cursor.execute("SELECT COUNT(*) FROM careers")
    total_careers = cursor.fetchone()[0]

    # Total Assessments
    cursor.execute("SELECT COUNT(*) FROM assessment")
    total_assessments = cursor.fetchone()[0]

    # Latest Students
    cursor.execute("""
        SELECT full_name, department, level
        FROM students
        ORDER BY id DESC
        LIMIT 5
    """)
    latest_students = cursor.fetchall()

    # Recent Assessments
    cursor.execute("""
        SELECT
            students.full_name,
            students.department,
            assessment.top_career
        FROM assessment
        JOIN students
        ON assessment.student_id = students.id
        ORDER BY assessment.id DESC
        LIMIT 5
    """)
    recent_assessments = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_analytics.html",
        total_students=total_students,
        total_careers=total_careers,
        total_assessments=total_assessments,
        latest_students=latest_students,
        recent_assessments=recent_assessments
    )

# ============================================================
# STUDENT DASHBOARD
# ============================================================

@app.route("/dashboard")
def dashboard():
    
    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""

        SELECT COUNT(*)

        FROM support_requests

        WHERE

            student_id=%s

            AND status='Resolved'

            AND is_read=0

    """,

    (

        session["user_id"],

    ))

    notification_count = cursor.fetchone()[0]

    cursor.close()

    return render_template(

        "dashboard.html",

        full_name=session.get("full_name"),

        email=session.get("email"),

        department=session.get("department"),

        level=session.get("level"),

        profile_picture=session.get("profile_picture", "default.png"),

        notification_count=notification_count

    )

#============================================================
#PROFILE
#============================================================
@app.route("/profile")
def profile():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute("""

    SELECT

    full_name,
    email,
    gender,
    date_of_birth,
    department,
    level,
    profile_picture

    FROM students

    WHERE id=%s

    """, (session["user_id"],))

    student = cursor.fetchone()

    cursor.close()

    return render_template(

    "profile.html",

    student=student

    )

# ============================================================
# EDIT PROFILE
# ============================================================

@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor(DictCursor)

    if request.method == "POST":

        full_name = request.form["full_name"]
        gender = request.form["gender"]
        date_of_birth = request.form["date_of_birth"]

        # Keep existing picture by default
        cursor.execute(
            "SELECT profile_picture FROM students WHERE id=%s",
            (session["user_id"],)
        )

        current_user = cursor.fetchone()

        profile_picture = current_user["profile_picture"]

        # Check if a new picture was uploaded
        if "profile_picture" in request.files:

            file = request.files["profile_picture"]

            if file and file.filename != "" and allowed_file(file.filename):

                result = cloudinary.uploader.upload(file)

                image_url = result["secure_url"]

                profile_picture = image_url

        cursor.execute("""

            UPDATE students

            SET

                full_name=%s,
                gender=%s,
                date_of_birth=%s,
                profile_picture=%s

            WHERE id=%s

        """, (

            full_name,
            gender,
            date_of_birth,
            profile_picture,
            session["user_id"]

        ))

        mysql.connection.commit()

        # Update session
        session["full_name"] = full_name
        session["profile_picture"] = profile_picture

        cursor.close()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(url_for("profile"))

    cursor.execute("""

        SELECT

            full_name,
            gender,
            date_of_birth,
            profile_picture

        FROM students

        WHERE id=%s

    """, (

        session["user_id"],

    ))

    student = cursor.fetchone()

    cursor.close()

    return render_template(

        "edit_profile.html",

        student=student

    )
    
# =====================================================
# DELETE CAREER
# =====================================================

@app.route("/admin/delete_career/<int:career_id>")
def admin_delete_career(career_id):

    cursor = mysql.connection.cursor()

    cursor.execute(
        "DELETE FROM careers WHERE id=%s",
        (career_id,)
    )

    mysql.connection.commit()

    cursor.close()

    flash(
        "Career deleted successfully.",
        "success"
    )

    return redirect(url_for("admin_manage_careers"))

# ============================================================
# BEHAVIOR ASSESSMENT
# ============================================================

@app.route("/behavior_assessment", methods=["GET", "POST"])
def behavior_assessment():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    cursor = mysql.connection.cursor()

    # ============================================================
    # SAVE ANSWERS
    # ============================================================

    if request.method == "POST":

        student_id = session["user_id"]

        # Remove previous answers
        cursor.execute("""

            DELETE FROM student_behavior_answers

            WHERE student_id=%s

        """, (

            student_id,

        ))

        # Only save displayed questions
        displayed_questions = request.form.getlist("displayed_questions")

        for question_id in displayed_questions:

            option_id = request.form.get(f"question_{question_id}")

            if option_id:

                cursor.execute("""

                    INSERT INTO student_behavior_answers
                    (

                        student_id,

                        question_id,

                        option_id

                    )

                    VALUES
                    (

                        %s,

                        %s,

                        %s

                    )

                """, (

                    student_id,

                    question_id,

                    option_id

                ))
                # ============================================================
                # CALCULATE BEHAVIOUR SCORES
                # ============================================================

                cursor.execute("""

                    DELETE FROM user_behavior_scores

                    WHERE user_id=%s

                """, (student_id,))


                cursor.execute("""

                    SELECT

                        bos.skill_id,

                        SUM(bos.points)

                    FROM student_behavior_answers sba

                    JOIN behavior_option_skills bos

                    ON sba.option_id = bos.option_id

                    WHERE sba.student_id=%s

                    GROUP BY bos.skill_id

                """, (student_id,))


                behavior_scores = cursor.fetchall()


                for skill_id, score in behavior_scores:

                    cursor.execute("""

                        INSERT INTO user_behavior_scores

                        (

                            user_id,

                            skill_id,

                            score

                        )

                        VALUES

                        (

                            %s,

                            %s,

                            %s

                        )

                    """, (

                        student_id,

                        skill_id,

                        score

                    ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Behavior Assessment Completed.",

            "success"

        )

        return redirect(

            url_for("recommendation")

        )

    # ============================================================
    # LOAD 30 RANDOM QUESTIONS
    # ============================================================

    cursor.execute("""

        SELECT

            id,

            question,

            category

        FROM behavior_questions

        ORDER BY RAND()

        LIMIT 30

    """)

    questions = cursor.fetchall()

    behavior_questions = []

    for question in questions:

        cursor.execute("""

            SELECT

                id,

                option_text

            FROM behavior_options

            WHERE question_id=%s

        """, (

            question[0],

        ))

        options = cursor.fetchall()

        behavior_questions.append({

            "id": question[0],

            "question": question[1],

            "category": question[2],

            "options": options

        })

    cursor.close()

    return render_template(

        "behavior_assessment.html",

        questions=behavior_questions

    )

# ============================================================
# SKILLS ASSESSMENT
# ============================================================

@app.route("/skills_assessment", methods=["GET", "POST"])
def skills_assessment():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(url_for("login"))

    student_id = session["user_id"]

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        # Remove previous assessment
        cursor.execute("""

            DELETE FROM student_skill_assessment

            WHERE student_id = %s

        """, (student_id,))

        # Load all skills
        cursor.execute("""

            SELECT

                id,
                skill_name

            FROM skills

            ORDER BY id

        """)

        skills = cursor.fetchall()

        # Save scores
        for skill in skills:

            skill_id = skill[0]

            score = int(

                request.form[f"skill_{skill_id}"]

            )

            cursor.execute("""

                INSERT INTO student_skill_assessment
                (
                    student_id,
                    skill_id,
                    score
                )

                VALUES
                (
                    %s,
                    %s,
                    %s
                )

            """, (

                student_id,
                skill_id,
                score

            ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Skills Assessment Completed.",

            "success"

        )

        return redirect(

            url_for("interest_assessment")

        )

    # ==========================================
    # LOAD SKILLS
    # ==========================================

    cursor.execute("""

        SELECT

            id,
            skill_name,
            description

        FROM skills

        ORDER BY skill_name

    """)

    skills = cursor.fetchall()

    cursor.close()

    return render_template(

        "skills_assessment.html",

        skills=skills

    )

# ============================================================
# INTEREST ASSESSMENT
# ============================================================

@app.route("/interest_assessment", methods=["GET", "POST"])
def interest_assessment():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(url_for("login"))

    student_id = session["user_id"]

    cursor = mysql.connection.cursor()

    if request.method == "POST":

        # Remove previous assessment
        cursor.execute("""

            DELETE FROM student_interest_assessment

            WHERE student_id = %s

        """, (student_id,))

        # Load all interests
        cursor.execute("""

            SELECT

                id,
                interest_name

            FROM interests

            ORDER BY id

        """)

        interests = cursor.fetchall()

        # Save scores
        for interest in interests:

            interest_id = interest[0]

            score = int(

                request.form[f"interest_{interest_id}"]

            )

            cursor.execute("""

                INSERT INTO student_interest_assessment
                (
                    student_id,
                    interest_id,
                    score
                )

                VALUES
                (
                    %s,
                    %s,
                    %s
                )

            """, (

                student_id,
                interest_id,
                score

            ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Interest Assessment Completed.",

            "success"

        )

        return redirect(

            url_for("behavior_assessment")

        )

    # ==========================================
    # LOAD INTERESTS
    # ==========================================

    cursor.execute("""
    SELECT
        id,
        interest_name
    FROM interests
""")

    interests = cursor.fetchall()

    cursor.close()

    return render_template(

        "interest_assessment.html",

        interests=interests

    )

# ============================================================
# RECOMMENDATION
# ============================================================

@app.route("/recommendation")
def recommendation():

    if "user_id" not in session:

        flash(
            "Please login first.",
            "warning"
        )

        return redirect(
            url_for("login")
        )

    student_id = session["user_id"]

    cursor = mysql.connection.cursor()

    # ============================================================
    # LOAD STUDENT TECHNICAL SKILLS
    # ============================================================

    cursor.execute("""

        SELECT
            skill_id,
            score

        FROM student_skill_assessment

        WHERE student_id = %s

    """, (student_id,))

    technical_scores = {

        row[0]: row[1]

        for row in cursor.fetchall()

    }

    # ============================================================
    # LOAD STUDENT INTERESTS
    # ============================================================

    cursor.execute("""

        SELECT
            interest_id,
            score

        FROM student_interest_assessment

        WHERE student_id = %s

    """, (student_id,))

    interest_scores = {

        row[0]: row[1]

        for row in cursor.fetchall()

    }

    # ============================================================
    # LOAD ALL CAREERS
    # ============================================================

    cursor.execute("""

        SELECT *

        FROM careers

    """)

    careers = cursor.fetchall()

    recommendations = []
        # ============================================================
    # CALCULATE RECOMMENDATIONS
    # ============================================================

    for career in careers:

        career_id = career[0]

        # --------------------------------------------------------
        # TECHNICAL SCORE
        # --------------------------------------------------------

        cursor.execute("""

            SELECT
                skill_id,
                importance

            FROM career_skills

            WHERE career_id = %s

        """, (career_id,))

        career_skills = cursor.fetchall()

        technical_total = 0
        technical_weight = 0

        for skill_id, importance in career_skills:

            student_score = technical_scores.get(skill_id, 0)

            technical_total += student_score * importance

            technical_weight += 5 * importance

        technical_percent = (
            (technical_total / technical_weight) * 100
            if technical_weight > 0
            else 0
        )

        # --------------------------------------------------------
        # INTEREST SCORE
        # --------------------------------------------------------

        cursor.execute("""

            SELECT
                interest_id,
                importance

            FROM career_interests

            WHERE career_id = %s

        """, (career_id,))

        career_interests = cursor.fetchall()

        interest_total = 0
        interest_weight = 0

        for interest_id, importance in career_interests:

            student_score = interest_scores.get(interest_id, 0)

            interest_total += student_score * importance

            interest_weight += 5 * importance

        interest_percent = (
            (interest_total / interest_weight) * 100
            if interest_weight > 0
            else 0
        )

        # --------------------------------------------------------
        # FINAL SCORE
        # --------------------------------------------------------

        final_score = (
            technical_percent * 0.60 +
            interest_percent * 0.40
        )

        confidence = round(
            (technical_percent + interest_percent) / 2,
            2
        )

        readiness = round(
            (
                final_score * 0.70 +
                confidence * 0.30
            ),
            2
        )

        recommendations.append({

            "career_id": career_id,

            "score": round(final_score, 2),

            "confidence": confidence,

            "readiness": readiness,

            "technical": round(technical_percent, 2),

            "interest": round(interest_percent, 2),    

        })
    # ============================================================
    # SORT RECOMMENDATIONS
    # ============================================================

    recommendations.sort(

        key=lambda x: (

            x["score"],

            x["confidence"]

        ),

        reverse=True

    )

    # ============================================================
    # KEEP TOP 5 CAREERS
    # ============================================================

    top5 = []

    for rank, rec in enumerate(recommendations[:5], start=1):

        cursor.execute("""

            SELECT

                career_name,

                career_field,

                description,

                why_fits,

                daily_responsibilities,

                required_skills,

                recommended_personality,

                activities_to_improve,

                certifications,

                learning_platforms,

                workplaces,

                industries,

                career_outlook,

                minimum_qualification,

                average_study_years,

                salary_note,

                did_you_know

            FROM careers

            WHERE id = %s

        """, (rec["career_id"],))

        career = cursor.fetchone()

        # --------------------------------------------------------
        # MATCH LEVEL
        # --------------------------------------------------------

        if rec["score"] >= 90:

            match_level = "Excellent Match"

            badge = "success"

        elif rec["score"] >= 80:

            match_level = "Very Good Match"

            badge = "primary"

        elif rec["score"] >= 70:

            match_level = "Good Match"

            badge = "info"

        elif rec["score"] >= 60:

            match_level = "Potential Match"

            badge = "warning"

        else:

            match_level = "Needs Improvement"

            badge = "secondary"

        # --------------------------------------------------------
        # READINESS STATUS
        # --------------------------------------------------------

        if rec["readiness"] >= 85:

            readiness_status = "Career Ready"

        elif rec["readiness"] >= 70:

            readiness_status = "Almost Ready"

        elif rec["readiness"] >= 50:

            readiness_status = "Developing"

        else:

            readiness_status = "Needs Improvement"

        top5.append({

            "rank": rank,

            "career_id": rec["career_id"],

            "career": career[0],

            "career_field": career[1],

            "description": career[2],

            "why_fits": career[3],

            "daily_responsibilities": career[4],

            "required_skills": career[5],

            "recommended_personality": career[6],

            "activities_to_improve": career[7],

            "certifications": career[8],

            "learning_platforms": career[9],

            "workplaces": career[10],

            "industries": career[11],

            "career_outlook": career[12],

            "minimum_qualification": career[13],

            "average_study_years": career[14],

            "salary_note": career[15],

            "did_you_know": career[16],

            "score": rec["score"],

            "confidence": rec["confidence"],

            "readiness": rec["readiness"],

            "technical": rec["technical"],

            "interest": rec["interest"],

            "match_level": match_level,

            "badge": badge,

            "readiness_status": readiness_status

        })
            # ============================================================
    # SAVE RECOMMENDATIONS
    # ============================================================

    cursor.execute("""

        DELETE FROM recommendations

        WHERE student_id = %s

    """, (student_id,))

    for rec in top5:

        cursor.execute("""

            INSERT INTO recommendations
            (

                student_id,

                career_id,

                match_percentage,

                confidence,

                rank_position

            )

            VALUES
            (

                %s,

                %s,

                %s,

                %s,

                %s

            )

        """, (

            student_id,

            rec["career_id"],

            rec["score"],

            rec["confidence"],

            rec["rank"]

        ))

    mysql.connection.commit()

    cursor.close()

    # ============================================================
    # DISPLAY RECOMMENDATIONS
    # ============================================================

    return render_template(

        "recommendation.html",

        recommendations=top5

    )

#============================================================
# ASSESSMENT HISTORY
# ============================================================
@app.route("/history")
def history():

    if "user_id" not in session:
        flash("Please login first.", "warning")
        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT
            id,
            assessment_date
        FROM assessment
        WHERE student_id=%s
        ORDER BY assessment_date DESC
    """, (session["user_id"],))

    history = cursor.fetchall()

    cursor.close()

    return render_template(
        "history.html",
        history=history
    )

# ============================================================
# ANALYTICS DASHBOARD
# ============================================================

@app.route("/analytics")
def analytics():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    cursor = mysql.connection.cursor()

    cursor.execute("""

    SELECT

    programming,
    mathematics,
    communication,
    leadership,
    creativity,
    problem_solving,
    teamwork,
    technology_interest,
    business_interest,
    healthcare_interest,
    analytical_thinking,
    research_interest,
    public_speaking,
    entrepreneurship,
    attention_to_detail

    FROM assessment

    WHERE student_id=%s

    ORDER BY id DESC

    LIMIT 1

    """,(session["user_id"],))

    assessment = cursor.fetchone()

    cursor.close()

    if not assessment:

        flash("Please complete an assessment first.","warning")

        return redirect (url_for("skills_assessment"))

    labels = [

        "Programming",
        "Mathematics",
        "Communication",
        "Leadership",
        "Creativity",
        "Problem Solving",
        "Teamwork",
        "Technology",
        "Business",
        "Healthcare",
        "Analytical",
        "Research",
        "Public Speaking",
        "Entrepreneurship",
        "Attention to Detail"

    ]

    values = list(assessment)

    highest = labels[values.index(max(values))]
    lowest = labels[values.index(min(values))]

    return render_template(

        "analytics.html",

        labels=labels,

        values=values,

        highest=highest,

        lowest=lowest

    )


# ============================================================
# DOWNLOAD RECOMMENDATION PDF
# ============================================================

@app.route("/download_pdf")
def download_pdf():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    student_id = session["user_id"]

    cursor = mysql.connection.cursor()

    # ============================================================
    # GET STUDENT DETAILS
    # ============================================================

    cursor.execute("""

        SELECT
            full_name,
            email,
            department,
            level

        FROM students

        WHERE id = %s

    """, (student_id,))

    student = cursor.fetchone()

    if not student:

        cursor.close()

        flash("Student record not found.", "danger")

        return redirect(url_for("dashboard"))

    # ============================================================
    # GET SAVED RECOMMENDATIONS
    # ============================================================

    cursor.execute("""

        SELECT

            r.match_percentage,

            r.confidence,

            r.rank_position,

            c.career_name,

            c.career_field,

            c.description,

            c.why_fits,

            c.required_skills,

            c.activities_to_improve,

            c.certifications,

            c.learning_platforms,

            c.workplaces,

            c.industries,

            c.career_outlook,

            c.minimum_qualification,

            c.average_study_years,

            c.salary_note,

            c.did_you_know

        FROM recommendations r

        JOIN careers c

        ON r.career_id = c.id

        WHERE r.student_id = %s

        ORDER BY r.rank_position ASC

    """, (student_id,))

    recommendations = cursor.fetchall()

    cursor.close()

    if not recommendations:

        flash("No recommendations available.", "warning")

        return redirect(url_for("recommendation"))

    # ============================================================
    # CREATE PDF
    # ============================================================

    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]
    title_style.alignment = TA_CENTER
    title_style.textColor = HexColor("#0d6efd")

    heading_style = styles["Heading2"]

    normal = styles["BodyText"]

    story = []

    # ============================================================
    # TITLE
    # ============================================================

    story.append(
        Paragraph(
            "Career Recommendation Report",
            title_style
        )
    )

    story.append(Spacer(1, 20))

    # ============================================================
    # STUDENT DETAILS
    # ============================================================

    story.append(
        Paragraph(
            "<b>Student Information</b>",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Name:</b> {student[0]}",
            normal
        )
    )

    story.append(
        Paragraph(
            f"<b>Email:</b> {student[1]}",
            normal
        )
    )

    story.append(
        Paragraph(
            f"<b>Department:</b> {student[2]}",
            normal
        )
    )

    story.append(
        Paragraph(
            f"<b>Level:</b> {student[3]}",
            normal
        )
    )

    story.append(Spacer(1, 20))

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    story.append(
        Paragraph(
            "<b>Top Career Recommendations</b>",
            heading_style
        )
    )

    story.append(Spacer(1, 10))

    for rec in recommendations:

        (
            match_percentage,
            confidence,
            rank,
            career_name,
            career_field,
            description,
            why_fits,
            required_skills,
            activities,
            certifications,
            platforms,
            workplaces,
            industries,
            outlook,
            qualification,
            study_years,
            salary,
            fact
        ) = rec

        story.append(
            Paragraph(
                f"<b>{rank}. {career_name}</b>",
                heading_style
            )
        )

        story.append(
            Paragraph(
                f"<b>Career Field:</b> {career_field}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Match Percentage:</b> {match_percentage:.2f}%",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Confidence:</b> {confidence:.2f}%",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Description:</b> {description}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Why It Fits:</b> {why_fits}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Required Skills:</b> {required_skills}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Activities to Improve:</b> {activities}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Certifications:</b> {certifications}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Learning Platforms:</b> {platforms}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Workplaces:</b> {workplaces}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Industries:</b> {industries}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Career Outlook:</b> {outlook}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Minimum Qualification:</b> {qualification}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Average Study Years:</b> {study_years}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Salary Information:</b> {salary}",
                normal
            )
        )

        story.append(
            Paragraph(
                f"<b>Did You Know?</b> {fact}",
                normal
            )
        )

        story.append(Spacer(1, 20))

    # ============================================================
    # BUILD PDF
    # ============================================================

    doc.build(story)

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name="Career_Recommendation_Report.pdf",

        mimetype="application/pdf"

    )


# ============================================================
# CONTACT ADMINISTRATOR
# ============================================================

@app.route("/contact_admin", methods=["GET", "POST"])
def contact_admin():

    if "user_id" not in session:

        flash("Please login first.", "warning")

        return redirect(url_for("login"))

    if request.method == "POST":

        subject = request.form["subject"]

        message = request.form["message"]

        cursor = mysql.connection.cursor()

        cursor.execute("""

            INSERT INTO support_requests

            (

                student_id,

                subject,

                message

            )

            VALUES

            (

                %s,

                %s,

                %s

            )

        """,

        (

            session["user_id"],

            subject,

            message

        ))

        mysql.connection.commit()

        cursor.close()

        flash(

            "Your request has been sent successfully.",

            "success"

        )

        return redirect(url_for("dashboard"))

    return render_template(

        "contact_admin.html"

    )

if __name__ == "__main__":
    app.run(debug=True) 