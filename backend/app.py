from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from flask import send_from_directory 

app = Flask(__name__)
app.secret_key = "jobportal"

UPLOAD_RESUME = "uploads/resumes"
UPLOAD_PHOTO = "uploads/photos"

app.config["UPLOAD_RESUME"] = UPLOAD_RESUME
app.config["UPLOAD_PHOTO"] = UPLOAD_PHOTO


def init_db():
    os.makedirs("static/uploads/photos", exist_ok=True)
    os.makedirs("static/uploads/resumes", exist_ok=True)
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    # USERS TABLE

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT,
    password TEXT,
    role TEXT
    )
    """)
    
    # JOBS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT,
    title TEXT,
    salary TEXT,
    location TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    description TEXT
    )
    """)
    
    #APPLICATIONS TABLE

    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER,
    student_name TEXT,
    resume TEXT,
    status TEXT DEFAULT  'pending'
    )
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS student_profile(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    address TEXT,
    dob TEXT,
    email TEXT,
    phone TEXT,
    degree TEXT,
    year TEXT,
    skills TEXT,
    photo TEXT,
    resume TEXT)""")
    
    
    cur.execute(""" CREATE TABLE IF NOT EXISTS notifications
    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
     user_id INTEGER,message TEXT)""")

    conn.commit()
    conn.close()

init_db()


@app.route("/home")
def home():
    return redirect("/login")


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        
        if not email.endswith("@gmail.com"):
            return "USE Gmail only!"
        
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
        (name,email,password,role))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["name"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
        "SELECT * FROM users WHERE name=? AND password=?",
        (username, password))

        user = cur.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]   
            session["role"] = user[4]
            session["user_id"] = user[0]
            
            if user[4] == "student":
                return redirect("/student")
            elif user[4] == "company":
                return redirect("/company")
            elif user[4] == "admin":
                return redirect("/admin")
            else:
                return redirect("/jobs")
        else:
            return "INVALID LOGIN"

    return render_template("login.html")


@app.route("/student")
def student():
    
    return render_template("student.html")


@app.route("/company")
def company():
     conn = sqlite3.connect("database.db")
     cur = conn.cursor()
     cur.execute("SELECT * FROM jobs")
     jobs = cur.fetchall()
     
     conn.close()
     return render_template("company.html",jobs=jobs)


@app.route("/admin")
def admin():
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM applications")
    applications = cur.fetchall()
    
    conn.close()
    
    return render_template("admin.html",applications=applications)

@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("DELETE FROM applications WHERE id=?", (id,))
    
    conn.commit()
    conn.close()
    
    return redirect("/admin")

@app.route("/jobs")
def jobs():
    
    if "user" not in session:
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM jobs")
    jobs = cur.fetchall()

    conn.close()

    return render_template("jobs.html", jobs=jobs,role=session["role"])


@app.route("/apply_job/<int:job_id>", methods=["POST"])
def apply(job_id):

    if "user" not in session:
        return redirect("/login")
    
    student_name = session["user"]
    user_id = session["user_id"]
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    resume = request.files.get("resume")

    if resume and resume.filename:
        resume_filename = resume.filename
        resume.save("static/uploads/resumes/" + resume_filename)
        
    else:
        resume_filename = None    
    
    cur.execute("SELECT * FROM applications WHERE job_id=? AND student_name=?",
                (job_id, student_name))
    if cur.fetchone():
            return "Already Applied!"
    
    cur.execute(""" INSERT INTO applications(job_id,student_name, resume,status)
                VALUES(?,?,?,?)""",(job_id, student_name,resume_filename,"Pending"))
    
     
    message = f"{student_name}  applied for job ID  {job_id}"
    
    cur.execute("""INSERT INTO notifications(user_id,message) VALUES(?,?)""",
                (user_id, message))
    
    conn.commit()
    conn.close()
    
    return redirect("/jobs")


@app.route("/my_applications")
def my_applications():
    
    user_id = session.get("user_id")
      
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT  
    applications.id,
    jobs.title, 
    jobs.location, 
    jobs.contact_email,
    jobs.contact_phone, 
    applications.resume,
    applications.status 
    FROM applications
    JOIN jobs ON applications.job_id = jobs.id """)

    applications = cur.fetchall()

    conn.close()

    return render_template("my_applications.html",applications=applications)

@app.route("/view_applicants")
def view_applicants():
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT  
    applications.id,
    applications.student_name,
    jobs.title, 
    jobs.location, 
    jobs.contact_email,
    jobs.contact_phone, 
    applications.resume,
    applications.status 
    FROM applications
    JOIN jobs ON applications.job_id = jobs.id """)

    applications = cur.fetchall()

    conn.close()

    return render_template("view_applications.html", applications=applications)


@app.route("/upload_resume", methods=["POST"])
def upload_resume():

    file = request.files["resume"]
    
    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)

    path = os.path.join(app.config["UPLOAD_RESUME"], filename)

    file.save(path)
    
    user_id = session.get("user_id")
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM student_profile WHERE user_id=?",
    (user_id,))
    data = cur.fetchone()
    
    if data:
        cur.execute("UPDATE student_profile SET resume=? WHERE user_id=?",
                         (filename, user_id))
        
    else:
        cur.execute("INSERT INTO student_profile(user_id,resume)VALUES(?,?)",
                        (user_id,filename))
        
    conn.commit()
    conn.close()
    return "Resume Uploaded"


@app.route("/upload_photo", methods=["POST"])
def upload_photo():

    file = request.files["photo"]
    
    if file.filename == "":
        return "No file selected"

    filename = secure_filename(file.filename)
    path = os.path.join(app.config["UPLOAD_PHOTO"], filename)

    file.save(path)
    
    user_id = session.get("user_id")
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM student_profile WHERE user_id=?",
    (user_id,))
    data = cur.fetchone()
    
    if data:
        cur.execute("UPDATE student_profile SET photo=? WHERE user_id=?",
                         (filename, user_id))
        
    else:
        cur.execute("INSERT INTO student_profile(user_id,photo)VALUES(?,?)",
                        (user_id,filename))
        
    conn.commit()
    conn.close()
        

    return redirect("/student_profile")


@app.route("/")
def splash():
    return render_template("splash.html")


@app.route("/loader")
def loader():
    return render_template("loader.html")

@app.route("/student_profile", methods=["GET", "POST"])
def student_profile():
    import os
    import sqlite3
    from flask import request, redirect, render_template

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    user_id = 1  # TODO: Replace with session user_id

    if request.method == "POST":
        name = request.form.get("name")
        address = request.form.get("address")
        dob = request.form.get("dob")
        email = request.form.get("email")
        phone = request.form.get("phone")
        degree = request.form.get("degree")
        year = request.form.get("year")
        skills = request.form.get("skills")

        photo = request.files.get("photo")
        resume = request.files.get("resume")

        # Create folders if not exists
        os.makedirs("static/uploads/photos", exist_ok=True)
        os.makedirs("static/uploads/resumes", exist_ok=True)

        photo_filename = None
        resume_filename = None

        # Save photo
        if photo and photo.filename != "":
            photo_filename = photo.filename
            photo.save(os.path.join("static/uploads/photos", photo_filename))

        # Save resume
        if resume and resume.filename !="":
            resume_filename = resume.filename
            resume.save(os.path.join("static/uploads/resumes", resume_filename))

        # Check existing profile
        cur.execute("SELECT * FROM student_profile WHERE user_id=?", (user_id,))
        existing = cur.fetchone()

        if existing:
            cur.execute("""
                UPDATE student_profile
                SET name=?, address=?, dob=?, email=?, phone=?, 
                degree=?,year=?, skills=?, photo=?, resume=?
                WHERE user_id=?
            """, (
                name, address, dob, email, phone,
                degree, year, skills, photo_filename, resume_filename, user_id
            ))
        else:
            cur.execute("""
                INSERT INTO student_profile
                (user_id, name, address, dob, email, phone, degree, year, skills, photo, resume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, name, address, dob, email,
                phone, degree, year, skills, photo_filename, resume_filename
            ))

        conn.commit()
        conn.close()

        return redirect("/student_profile")

    # GET request
    cur.execute("SELECT * FROM student_profile WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    conn.close()

    return render_template("student_profile.html", data=data)    
        
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/uploads/resumes/<filename>')
def download_file(filename):
    return send_from_directory(app.config["UPLOAD_RESUME"],filename)

@app.route('/uploads/photos/<filename>')
def view_photo(filename):
    return send_from_directory(app.config['UPLOAD_PHOTO'], filename)

@app.route("/post_job", methods=["GET","POST"])
def post_job():
    if request.method == "POST":
        company_name = request.form["company_name"]
        title = request.form["title"]
        salary = request.form["salary"]
        location = request.form["location"]        
        contact_email = request.form["contact_email"]
        contact_phone = request.form["contact_phone"]        
        description = request.form["description"]
        
        company_id = session.get("user_id")
        
        conn  = sqlite3.connect("database.db")
        cur = conn.cursor()
        
        cur.execute(""" INSERT INTO jobs(company_name,
        title, salary, location, contact_email, contact_phone, description) VALUES(?,?,?,?,?,?,?)""",
            (company_name, title, salary, location, contact_email, contact_phone,description))
        
        cur.execute("INSERT INTO notifications(user_id, message) VALUES(?,?)""",
                    (company_id, "NEW job Posted"))
                        
         
        conn.commit()
        conn.close()
         
        return redirect("/jobs")
     
    return render_template("post_job.html")

@app.route("/update_status/<int:id>",methods=["POST"])
def update_status(id):
    if "user" not in session:
        return redirect("/login")
    
    status = request.form.get("status")
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("UPDATE applications SET status=? WHERE id=?", (status, id))

    
    conn.commit()
    conn.close()
    
    return redirect("/view_applicants")

@app.route("/notifications")
def notifications():
    
    if "user" not in session:
        return redirect("/login")
    
    user_id = session.get("user_id")
    
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    cur.execute("SELECT *  FROM notifications WHERE user_id=?", (user_id,))
    data = cur.fetchall()
    
    conn.close()
    
    return render_template("notifications.html", notifications=data)
 
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
