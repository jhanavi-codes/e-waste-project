import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ewaste.db")


from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
       CREATE TABLE IF NOT EXISTS requests (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       user_id INTEGER,
       fullname TEXT NOT NULL,
       device_type TEXT NOT NULL,
       quantity TEXT NOT NULL,
       address TEXT NOT NULL,
       pickup_date TEXT NOT NULL,
       status TEXT DEFAULT 'Pending',
       employee_name TEXT
       )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT NOT NULL,
         password TEXT NOT NULL
        )
    """)


    cur.execute("""
        CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        area TEXT NOT NULL,
        status TEXT DEFAULT 'Available'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS login (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()


# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("index.html", user=session.get("user"))

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        try:
            cur.execute("INSERT INTO users (fullname, email, phone, password) VALUES (?, ?, ?, ?)",
                        (fullname, email, phone, password))
            conn.commit()
            conn.close()
            return "Registration Successful! <br><br><a href='/login'>Go to Login</a>"
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered! <br><br><a href='/register'>Try Again</a>"

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = email
            return redirect("/request")
        else:
            return "Invalid Email or Password! <br><br><a href='/login'>Try Again</a>"

    return render_template("login.html")

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["user"] = "admin"
            return redirect("/admin")
        else:
            return "Invalid Admin Credentials"

    return render_template("admin_login.html")

# ---------- PICKUP REQUEST ----------
@app.route("/request", methods=["GET", "POST"])
def pickup_request():

    # 🔐 LOGIN CHECK (MUST BE FIRST LINE)
    if not session.get("user"):
        return redirect("/login")

    if request.method == "POST":
        fullname = session.get("user")
        device_type = request.form.get("device_type")
        quantity = request.form.get("quantity")
        address = request.form.get("address")
        pickup_date = request.form.get("pickup_date")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO requests (fullname, device_type, quantity, address, pickup_date, status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
        """, (fullname, device_type, quantity, address, pickup_date))

        conn.commit()
        conn.close()

        return "Pickup Request Submitted!"

    return render_template("request.html")

# ---------- ADMIN DASHBOARD ----------
@app.route("/admin")
def admin():
    if session.get("user") != "admin":
        return redirect("/admin_login")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # requests
    cur.execute("""
    SELECT r.id, u.fullname, r.device_type, r.quantity, r.pickup_date, r.status,
    e.name as employee_name
    FROM requests r
    LEFT JOIN users u ON r.user_id = u.id
    LEFT JOIN employees e ON r.employee_name = e.name
    """)
    requests = cur.fetchall()

    cur.execute("SELECT id, email FROM users")
    users = cur.fetchall()

    conn.close()

    return render_template("admin.html", requests=requests, users=users)

@app.route("/remove_employee")
def remove_employee():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT id, name, phone, area FROM employees")
    employees = cur.fetchall()

    conn.close()

    return render_template("remove_employee.html", employees=employees)


@app.route("/delete_employee/<int:id>")
def delete_employee(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DELETE FROM employees WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect("/remove_employee")

@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        area = request.form["area"]

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO employees (name, phone, area) VALUES (?, ?, ?)",
            (name, phone, area)
        )
        conn.commit()
        conn.close()

        return "Employee Added Successfully! <br><br><a href='/admin'>Back to Admin Dashboard</a>"

    return render_template("add_employee.html")

@app.route("/view_employees")
def view_employees():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name, phone, area, status FROM employees")
    employees = cur.fetchall()
    conn.close()

    return render_template("view_employees.html", employees=employees)
   

@app.route("/assign/<int:id>", methods=["GET", "POST"])
def assign_employee(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if request.method == "POST":
        employee = request.form["employee"]

        cur.execute("""
        UPDATE requests 
        SET employee_name=?, status='Assigned'
        WHERE id=?
        """, (employee, id))

        conn.commit()
        conn.close()

        return redirect("/admin")

    # 👇 FETCH EMPLOYEES
    cur.execute("SELECT name FROM employees")
    employees = cur.fetchall()

    # 👇 FETCH REQUESTS
    cur.execute("SELECT id FROM requests")
    requests = cur.fetchall()

    conn.close()

    return render_template(
        "assign_page.html",
        employees=employees,
        requests=requests
    )


@app.route("/update_status/<int:req_id>", methods=["POST"])
def update_status(req_id):
    if session.get("user") != "admin":
        return redirect("/admin_login")

    status = request.form.get("status")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE requests SET status=? WHERE id=?", (status, req_id))
    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get("user") != "admin":
        return redirect("/admin_login")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE rowid=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect("/admin")

@app.route("/remove_user")
def remove_user():
    if session.get("user") != "admin":
        return redirect("/admin_login")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT rowid, email FROM users")
    users = cur.fetchall()
    print("USERS DATA:", users)

    conn.close()

    return render_template("remove_user.html", users=users)


@app.route("/check_users")
def check_users():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users")
    data = cur.fetchall()

    conn.close()
    return str(data)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

    # GET request → show employees list
    cur.execute("SELECT name FROM employees")
    employees = cur.fetchall()
    conn.close()

    return render_template("assign_employee.html", employees=employees, req_id=req_id)

    return render_template("view_employees.html", employees=employees)
if __name__ == "__main__":
    init_db()
    app.run(debug=True)