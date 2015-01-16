from flask import Flask, url_for, render_template, session, request, redirect
from flask.ext.sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import appsecret
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = appsecret.DBURI
app.secret_key = appsecret.SECRETKEY
app.jinja_env.autoescape = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    ip = db.Column(db.String(15))
    pw_hash = db.Column(db.String(66))

    def __init__(self, username, email, password, ip):
        self.username = username
        self.email = email
        self.set_password(password)
        self.ip = ip

    def set_password(self, password):
        self.pw_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def __repr__(self):
        return '<User %r>' % self.username

class Watch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer)
    tv = db.Column(db.Boolean)
    name = db.Column(db.String(300))
    ep = db.Column(db.String(15), nullable=True)

    def __init__(self, tv, name, ep):
        self.tv = tv
        self.name = name
        self.ep = ep

    def __repr__(self):
        if self.tv:
            return '<TV %s %s>' % (self.name, self.ep)
        else:
            return '<Movie %s>' % self.name

@app.route("/")
def index():
    return render_template("base.html", content="Hello! I'm a little trakt.tv alternative, short and stout. API in progress.", name=session.get('username', None))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        new_user = User(request.form['name'],
                        request.form['email'],
                        request.form['password'],
                        request.headers.getlist("X-Forwarded-For")[0])
        db.session.add(new_user)
        db.session.commit()
        session['userid'] = new_user.id
        session['username'] = new_user.username
        return render_template("base.html", content=render_template('register_complete.html'), title="Registration complete", name=session.get('username', None))
    return render_template("base.html", content=render_template('register.html'), title="Register", name=session.get('username', None))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    if not "username" in session:
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['name']).first()
            if user and user.check_password(request.form['password']):
                session['userid'] = user.id
                session['username'] = user.username
                return render_template("base.html", content=render_template("login_success.html"), title="Login succeeded", name=session.get('username', None))
            return render_template("base.html", content=render_template("login_failed.html") + render_template("login.html"), title="Login failed", name=session.get('username', None))
        else:
            return render_template("base.html", content=render_template("login.html"), title="Login", name=session.get('username', None))
    return redirect('/')

@app.route('/logout/')
def logout():
    if "username" in session:
        session.pop('userid', None)
        session.pop('username', None)
    return redirect('/')

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
