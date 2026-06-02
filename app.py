from flask import Flask, render_template, url_for, request, session, redirect
import sqlite3
import plotly.express as px
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "kool"



# ---------------------------
# DATABASE SETUP
# ---------------------------

connection = sqlite3.connect("/data/mydb.db")
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        grade INTEGER,
        password TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS mail (
        id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE,
        reciever TEXT NOT NULL,
        message TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS lost_request (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_name TEXT NOT NULL,
        description TEXT NOT NULL,
        photo TEXT,
        date_lost TEXT,
        bystudent TEXT NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS found_request (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_name TEXT NOT NULL,
        description TEXT NOT NULL,
        photo TEXT,
        date_lost TEXT,
        bystudent TEXT NOT NULL
    )
''')


connection.commit()
connection.close()


# ---------------------------
# HELPERS
# ---------------------------

def get_items():

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute("SELECT * FROM lost_request")

    lost_items = curr.fetchall()

    curr.execute("SELECT * FROM found_request")

    found_items = curr.fetchall()


    conn.close()

    return lost_items,found_items


# ---------------------------
# ROUTES
# ---------------------------

@app.route("/")
def home():
    return render_template("home.html")


@app.route('/register', methods=['POST'])
def register():
    return render_template("register.html")


@app.route('/make_acc', methods=['POST'])
def make_acc():

    uname = request.form.get('name')
    pw = request.form.get('password')
    grade = request.form.get('grade')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    try:

        curr.execute(
            "INSERT INTO users (name, grade, password) VALUES (?, ?, ?)",
            (uname, grade, pw)
        )

        conn.commit()

    except sqlite3.IntegrityError:

        print("Username already exists")

    finally:

        conn.close()

    return redirect(url_for("login"))


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")


@app.route('/clogin', methods=['POST'])
def clogin():

    uname = request.form.get('name')
    pw = request.form.get('password')
    grade = request.form.get('grade')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute(
        "SELECT name, password,grade FROM users WHERE name = ?",
        (uname,)
    )

    row = curr.fetchone()

    conn.close()

    user_found = row[0] if row else None
    user_password_sql = row[1] if row else None

    if user_found and user_password_sql == pw:

        session["user"] = user_found

        print(f"{user_found} logged in properly")

        return redirect(url_for("portal"))

    return "Invalid Credentials", 401

@app.route('/portal')
def portal():

    if "user" not in session:
        return redirect(url_for("home"))

    lost_items, found_items = get_items()

    return render_template(
        "portal.html",
        lost_items=lost_items,
        found_items=found_items,
        username=session["user"]
    )

@app.route('/registerlr', methods=['POST'])
def makereql():

    curruser = session.get("user")

    if not curruser:
        return "Login Required", 401

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    artn = request.form.get('article-name')
    desc = request.form.get('description')
    date = request.form.get('date')

    photo = request.files.get('photo')

    filename = None

    if photo and photo.filename:

        filename = photo.filename

        photo.save(f"/data/uploads/{filename}")

    curr.execute(
        """
        INSERT INTO lost_request
        (article_name, description, photo, date_lost, bystudent)
        VALUES (?, ?, ?, ?, ?)
        """,
        (artn, desc, filename, date, curruser)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("portal"))




@app.route('/registerr', methods=['POST'])
def makereqf():

    curruser = session.get("user")

    if not curruser:
        return "Login Required", 401

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    artn = request.form.get('article-name')
    desc = request.form.get('description')
    date = request.form.get('date')

    photo = request.files.get('photo')

    filename = None

    if photo and photo.filename:

        filename = photo.filename

        photo.save(f"/data/uploads/{filename}")

    curr.execute(
        """
        INSERT INTO found_request
        (article_name, description, photo, date_lost, bystudent)
        VALUES (?, ?, ?, ?, ?)
        """,
        (artn, desc, filename, date, curruser)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("portal"))


@app.route('/logout', methods=['POST'])
def logout():

    session.clear()

    return redirect(url_for("home"))

@app.route('/gotol', methods=['POST'])
def gotol():
    return render_template('add_lost_request.html')

@app.route('/gotof', methods=['POST'])
def gotof():
    return render_template('add_found_request.html')


# 1. Fixed route syntax: added leading slash and changed 'method' to 'methods'
@app.route('/foundit', methods=['POST'])
def sendmail():
    curruser = session.get("user")
    lost_item_id = request.form.get('item_id')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute(
    "SELECT * FROM lost_request WHERE id = ?",
    (lost_item_id,)
)
    
    lost_item = curr.fetchone()

    curr.execute(
    "SELECT article_name FROM lost_request WHERE id = ?",
    (lost_item_id,)
)
    
    lost_iname = curr.fetchone()[0]

    curr.execute(
    "SELECT bystudent FROM lost_request WHERE id = ?",
    (lost_item_id,)
    )

    madeby = curr.fetchone()[0]

    message = f"{curruser} found your {lost_iname} on {datetime.now().strftime('%Y-%m-%d')} you both can meet and discuss it in school!"

    # 5. Insert variables into your found_request table
    curr.execute(""" 
        INSERT INTO mail (reciever, message) 
        VALUES (?, ?)
    """, (madeby, message))

    # 6. Commit the changes and close the connection
    conn.commit()
    conn.close()
     
    print("Received ID:", lost_item_id)
    # 7. Always return a valid response to avoid Flask routing errors
    return redirect(url_for('portal'))

@app.route("/mail", methods=['POST'])
def mail():
    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute(
        "SELECT * FROM mail WHERE reciever = ?",
        (session["user"],)
    )

    mails = curr.fetchall()

    return render_template(
        "mail.html",
        mails=mails,
        username=session["user"]
    )

@app.route("/admpn", methods=['POST'])
def adminpanel():

    if session.get("user", "").lower() in ["adminsmis", "krishna"]:

        conn = sqlite3.connect("/data/mydb.db")
        curr = conn.cursor()

        curr.execute("SELECT * FROM users")
        users = curr.fetchall()

        curr.execute("SELECT * FROM lost_request")
        lost_requests = curr.fetchall()

        curr.execute("SELECT * FROM found_request")
        found_requests = curr.fetchall()

        totalusers = len(users)
        totallrequests = len(lost_requests)
        totalfrequests = len(found_requests)

        grade_counts = {}

        for user in users:
            grade = user[2]

            if grade in grade_counts:
                grade_counts[grade] += 1
            else:
                grade_counts[grade] = 1

        conn.close()

        fig = px.bar(
        x=["Users", "Lost Articles", "Found Articles"],
        y=[totalusers, totallrequests, totalfrequests],
        text=[totalusers, totallrequests, totalfrequests]
        )

        fig.update_layout(
        title="Portal Statistics",
        xaxis_title="Category",
        yaxis_title="Count",
        height=400,
        width=400,
        margin=dict(l=20, r=20, t=50, b=20)
        )

        fig2 = px.pie(
        title="Portal Distrubution",
        names=["Found", "Lost", "Users"],
        values=[totalfrequests, totallrequests, totalusers],
        width=400,
        height=400
        )


        fig.update_traces(
        textposition="outside"
        )

        fig3 = px.bar(
        x=list(grade_counts.keys()),
        y=list(grade_counts.values()),
        title="Users by Grade",
        labels={
            "x": "Grade",
            "y": "Students"
        },
        height=400,
        width=400
        )

        graph_html3 = fig3.to_html(full_html=False)
        c2_html = fig2.to_html(full_html=False)
        graph_html = fig.to_html(full_html=False)

        return render_template(
        "adminportal.html",
        totalusers=totalusers,
        totallost=totallrequests,
        totalfound=totalfrequests,
        users=users,
        lost_requests=lost_requests,
        found_requests=found_requests,
        graph=graph_html,
        chart=c2_html,
        c2=graph_html3
        )
    
    else:
        return "Only Admins Can Use The Admin Portal"
    
@app.route("/deleteuser" ,  methods=['POST'])
def deluser():
    id = request.form.get('id')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute("DELETE FROM users WHERE id = ?",
    (id,)
    )

    conn.commit()
    conn.close()


    return redirect(url_for("portal"))

@app.route("/deletelostreq" ,  methods=['POST'])
def dellost():
    id = request.form.get('id')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute("DELETE FROM lost_request WHERE id = ?",
    (id,)
    )

    conn.commit()
    conn.close()


    return redirect(url_for("portal"))

@app.route("/deletefound" ,  methods=['POST'])
def delfound():
    id = request.form.get('id')

    conn = sqlite3.connect("/data/mydb.db")
    curr = conn.cursor()

    curr.execute("DELETE FROM found_request WHERE id = ?",
    (id,)
    )

    conn.commit()
    conn.close()


    return redirect(url_for("portal"))
 




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)