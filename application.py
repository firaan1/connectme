import os
import hashlib
import json
from datetime import datetime

from flask import Flask, session, render_template, request, flash, redirect, url_for, abort, g
from flask_session import Session
from flask_socketio import SocketIO, emit

from functools import wraps

app = Flask(__name__)

# jinja2
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

Session(app)

users_dict = {}

channels_dict = {}

max_posts = 100

app_init = 1

# taken from flask webpage decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] is None or not session['logged_in']:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def logout_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session['logged_in'] :
            return render_template('error.html', message = "User already logged in!")
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def before_request():
    global app_init
    if app_init == 1:
        app_init = 0
        session['logged_in'] = False
        g.initvar = True
    else:
        g.initvar = False

@app.route("/")
def index():
    try:
        session['logged_in']
    except:
        session['logged_in'] = False
    return render_template('index.html', users_dict = json.dumps(users_dict), sessionid = session['logged_in'], channels_dict = channels_dict)

@app.route("/forgotpassword", methods = ["GET", "POST"])
@logout_required
def forgotpassword():
    if request.method == "POST":
        todo = request.form.get('todo')
        if todo == "username":
            username = request.form.get('username')
            try:
                if users_dict[username]:
                    question = users_dict[username]['question'] + "?"
                    return render_template('forgotpassword.html', message = username, question = question)
                else:
                    return render_template('error.html', message = "User does not exist")
            except:
                return render_template('error.html', message = "User does not exist")
        elif todo == "changepassword":
            username = request.form.get('username')
            password = request.form.get('password')
            password_retype = request.form.get('password_retype')
            answer = request.form.get('answer')
            if not password == password_retype:
                return render_template('error.html', message = "Check retyping password")
            password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
            try:
                if users_dict[username]:
                    if users_dict[username]['answer'] != answer:
                        return render_template('error.html', message = "Incorrect answer")
                    users_dict[username]['password'] = password_hash
                    return render_template('forgotpassword.html', message = "Password Changed Successfully")
                else:
                    return render_template('error.html', message = "User does not exist")
            except:
                return render_template('error.html', message = "User does not exist")
    return render_template('forgotpassword.html')

@app.route("/settings", methods = ["GET","POST"])
@login_required
def settings():
    if request.method == "POST":
        global users_dict, channels_dict
        todo = request.form.get('todo')
        if todo == "changepassword":
            username = request.form.get('username')
            password = request.form.get('password')
            password_retype = request.form.get('password_retype')
            if not password == password_retype:
                return render_template('error.html', message = "Check retyping password")
            password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
            try:
                if users_dict[username]:
                    users_dict[username]['password'] = password_hash
                    return render_template('settings.html', message = "Password Changed Successfully")
                else:
                    return render_template('error.html', message = "User does not exist")
            except:
                return render_template('error.html', message = "User does not exist")
        elif todo == "deleteaccount":
            username = request.form.get('username')
            try:
                if users_dict[username]:
                    tmp_channels_dict = json.loads(json.dumps(channels_dict))
                    for c in channels_dict:
                        if channels_dict[c]['owner'] == username:
                            tmp_channels_dict.pop(c)
                    channels_dict = tmp_channels_dict
                    users_dict.pop(username)
                    session['logged_in'] = False
                    session['logged_pass'] = False
                    return redirect(url_for('index'))
                else:
                    return render_template('error.html', message = "User does not exist")
            except:
                return render_template('error.html', message = "User does not exist")
    return render_template('settings.html')

@app.route("/channels", methods = ["GET", "POST"])
@login_required
def channels():
    return render_template('channels.html', channels_dict = json.dumps(channels_dict), user_dict = json.dumps(users_dict[session['logged_in']]))

@app.route("/addchannel", methods = ["POST"])
@login_required
def addchannel():
    channel_info = json.loads(request.form.get("channel_info"))
    users_dict[session['logged_in']]['channels_user'].append(list(channel_info.keys())[0])
    users_dict[session['logged_in']]['channels_owner'].append(list(channel_info.keys())[0])
    channels_dict.update(json.loads(request.form.get("channel_info")))
    return redirect(url_for('channels'))

@socketio.on("submit post")
def post(data):
    post_text = data['post_text']
    channel = data['channel']
    posts = channels_dict[channel]['channel_messages']
    if not posts:
        index = 0
    else:
        indexes = sorted(list(posts.keys()))
        index = indexes[-1] + 1
        index_rm = indexes[0]
        if len(posts) == max_posts:
            posts.pop(index_rm)
    post_dict = {
    index : {
        'user' : session['logged_in'],
        'message' : post_text,
        'date' : datetime.now().strftime("%Y-%m-%d"),
        'time' : datetime.now().strftime("%H:%M:%S"),
        'index' : index
        }
    }
    posts.update(post_dict)
    emit("post list", json.dumps(post_dict), broadcast=True)

@socketio.on("delete post")
def delpost(data):
    post_index = int(data['post_index'])
    channel = data['channel']
    channels_dict[channel]['channel_messages'].pop(post_index)
    current_post = json.dumps({'channel' : channel, 'post_index' : post_index})
    emit("post delete", current_post, broadcast=True)

@app.route("/modchannel", methods = ["POST"])
@login_required
def modchannel():
    channel = request.form.get('current_channel')
    button = request.form.get('button')
    if button == 'delete':
        channels_dict.pop(channel)
        users_dict[session['logged_in']]['channels_user'].remove(channel)
        users_dict[session['logged_in']]['channels_owner'].remove(channel)
    elif button == 'leave':
        users_dict[session['logged_in']]['channels_user'].remove(channel)
    elif button == 'join':
        users_dict[session['logged_in']]['channels_user'].append(channel)
    return redirect(url_for('channels'))

@app.route("/channels/<string:channel>")
@login_required
def channel(channel):
    if channel not in channels_dict:
        return render_template('error.html', message = "Unknown channel")
    if channel not in users_dict[session['logged_in']]['channels_user']:
        return render_template('error.html', message = "Join the channel to access it")
    channel_posts = channels_dict[channel]['channel_messages']
    return render_template('channel.html', channels_dict = json.dumps(channels_dict), channel = channel, max_posts = max_posts)

@app.route("/login", methods = ["GET", "POST"])
@logout_required
def login():
    if request.method == "POST":
        session_logged_in = request.form.get('session_logged_in')
        username = request.form.get('username')
        password = request.form.get('password')
        if session_logged_in:
            session_logged_in = json.loads(session_logged_in)
            username = session_logged_in['user']
            password_hash = session_logged_in['password']
        else:
            password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        if not users_dict:
            return render_template('error.html', message = "Unknown user")
        for user in users_dict:
            if user == username:
                if users_dict[user]['password'] == password_hash:
                    session['logged_in'] = username
                    session['logged_pass'] = password_hash
                else:
                    return render_template('error.html', message = "Check user credentials")
        if not session['logged_in']:
            return render_template('error.html', message = "Unknown user")
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route("/logout", methods = ["GET", "POST"])
@login_required
def logout():
    session['logged_in'] = False
    session['logged_pass'] = False
    return redirect(url_for('index'))

@app.route("/register", methods = ["GET", "POST"])
@logout_required
def register():
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        password_retype = request.form.get('password_retype')
        question = request.form.get('question')
        answer = request.form.get('answer')
        if not password == password_retype:
            return render_template('error.html', message = "Check retyping password")
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()

        # adding users
        if users_dict:
            for user in users_dict:
                if user == username:
                    return render_template('error.html', message = "User already exists")
        users_dict[username] = {
        'password' : password_hash,
        'channels_user' : [],
        'channels_owner' : [],
        'question' : question,
        'answer' : answer
        }
        session['logged_in'] = username
        session['logged_pass'] = password_hash
        return redirect(url_for('index'))
    return render_template('register.html')
