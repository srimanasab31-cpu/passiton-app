from flask import Flask, render_template, request, redirect, session
import json
import random

app = Flask(__name__)
app.secret_key = "passiton_secret"

DATA_FILE = "data.json"


def read_data():
    with open(DATA_FILE) as f:
        return json.load(f)


def write_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def get_user(data, email):
    for user in data["users"]:
        if user["email"] == email:
            return user
    return None


@app.route("/", methods=["GET","POST"])
def login():

    data = read_data()

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        captcha = request.form["captcha"]

        if captcha != session["captcha"]:
            return "Captcha incorrect"

        user = get_user(data,email)

        if user and user["password"] == password:
            session.clear()
            session["email"] = email
            return redirect("/dashboard")

        return "Invalid login"

    n1 = random.randint(1,9)
    n2 = random.randint(1,9)

    session["captcha"] = str(n1+n2)

    return render_template("login.html",question=f"{n1}+{n2}")


@app.route("/register",methods=["GET","POST"])
def register():

    if request.method == "POST":

        data = read_data()

        new_user = {
        "name": request.form["name"],
        "email": request.form["email"],
        "password": request.form["password"],
        "points": 0
        }

        data["users"].append(new_user)

        write_data(data)

        return redirect("/")

    return render_template("register.html")



@app.route("/dashboard")
def dashboard():

    if "email" not in session:
        return redirect("/")

    data = read_data()
    user = get_user(data, session["email"])

    count = len([r for r in data["requests"] 
                 if r["owner"] == session["email"] and r["status"] == "pending"])

    return render_template("dashboard.html", user=user, count=count)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/donate",methods=["GET","POST"])
def donate():

    data = read_data()
    user = get_user(data,session["email"])

    if request.method == "POST":

        type = request.form["type"]

        if type == "note":

            course = request.form.get("course")
            content = request.form.get("content")

            if course and content:

                data["notes"].append({
                    "course":course,
                    "content":content,
                    "owner":user["email"],
                    "available":True
                })

                user["points"] += 10


        if type == "book":

            book = request.form.get("book")
            author = request.form.get("author")

            if book and author:

                data["books"].append({
                    "book":book,
                    "author":author,
                    "owner":user["email"],
                    "available":True
                })

                user["points"] += 10

        write_data(data)

        return redirect("/dashboard")

    return render_template("donate.html")


@app.route("/search")
def search():

    data = read_data()

    books = [b for b in data["books"] if b["available"]]
    notes = [n for n in data["notes"] if n["available"]]

    return render_template("search.html",books=books,notes=notes)


@app.route("/request/<type>/<name>/<owner>")
def request_book(type,name,owner):

    data = read_data()
    user = get_user(data,session["email"])

    data["requests"].append({

        "type":type,
        "name":name,
        "owner":owner,
        "requester":user["email"],
        "points":user["points"],
        "status":"pending",
        "place":"",
        "time":"",
        "contact":""

    })

    write_data(data)

    return redirect("/dashboard")


@app.route("/notifications", methods=["GET","POST"])
def notifications():

    # 🔥 FIX: check login FIRST
    if "email" not in session:
        return redirect("/")

    data = read_data()
    owner = session["email"]

    req = [r for r in data["requests"] 
           if r["owner"] == owner and r["status"] == "pending"]

    req = sorted(req, key=lambda x: x["points"], reverse=True)

    if request.method == "POST":

        selected = request.form["user"]
        place = request.form["place"]
        time = request.form["time"]
        contact = request.form["contact"]

        for r in data["requests"]:
            if r["owner"] == owner and r["status"] == "pending":

                if r["requester"] == selected:
                    r["status"] = "approved"
                    r["place"] = place
                    r["time"] = time
                    r["contact"] = contact
                else:
                    r["status"] = "rejected"

        write_data(data)

        return redirect("/dashboard")

    return render_template("notifications.html", requests=req)
@app.route("/leaderboard")
def leaderboard():

    data = read_data()

    users = sorted(data["users"],key=lambda x:x["points"],reverse=True)

    return render_template("leaderboard.html",users=users)


@app.route("/tracking")
def tracking():

    if "email" not in session:
        return redirect("/")

    data = read_data()
    user = session["email"]

    req = []

    for r in data["requests"]:
        if r.get("requester") == user or r.get("owner") == user:
            req.append(r)

    return render_template("tracking.html", requests=req)

@app.route("/profile")
def profile():

    data = read_data()
    user = get_user(data,session["email"])

    return render_template("profile.html",user=user)
app.config['SESSION_COOKIE_SAMESITE'] = "Lax"
app.config['SESSION_COOKIE_SECURE'] = False


if __name__ == "__main__":
    port=int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0",port=port)
