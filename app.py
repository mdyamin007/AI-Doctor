from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import cross_origin, CORS
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_socketio import SocketIO, join_room, leave_room
import datetime
from dbchat import save_message, get_messages

app = Flask(__name__)
app.secret_key = '09cd6cb8206a12b54a7ddb28566be757'
socketio = SocketIO(app, cors_allowed_origins="*")
bcrypt = Bcrypt(app)

cluster = MongoClient(
        "mongodb+srv://mdyamin:yamin787898@cluster0.5bduk.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
db = cluster['aidoctor']

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/bot')
@cross_origin()
def chat_bot():
    if "email" in session:
        return render_template('bot.html')
    else:
        return redirect(url_for('login', next='/bot'))

@app.route('/dashboard')
@cross_origin()
def dashboard():
    if "email" in session:
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))

@app.route('/profile')
@cross_origin()
def profile():
    return render_template('profile.html')

@app.route('/settings', methods=['GET', 'POST'])
@cross_origin()
def settings():
    if request.method == "GET":
        return render_template('settings.html')
    else:
        collection = db['users']
        form_data = request.form
        query_data = {
            "email": form_data['email']
        }
        result = collection.find_one(query_data)
        response = ''
        if bcrypt.check_password_hash(result['password'], form_data['current_password']) == True:
            update_data = {
                "name": form_data['name'],
                "password": bcrypt.generate_password_hash(form_data['new_password1']).decode('utf-8'),
                "userType": form_data['userType']
            }
            result = collection.find_one_and_update(query_data, { "$set" : update_data })
            if result:
                response = 'succeeded'
                session['name'] = form_data['name']
                session['userType'] = form_data['userType']
        else:
            response = 'failed'
        return render_template('settings.html', response=response)

@app.route('/contact')
@cross_origin()
def contact_us():
    return render_template('contactUs.html')

@app.route('/services')
@cross_origin()
def services():
    return render_template('services.html')

@app.route('/signup', methods=['POST'])
@cross_origin()
def sign_up():
    collection = db['users']
    form_data = request.form
    pw_hash =  bcrypt.generate_password_hash(form_data['password']).decode('utf-8')
    result = collection.find_one({'email': form_data['email']})
    if result == None:
        id = collection.insert_one({
            'name': form_data['name'],
            'email': form_data['email'],
            'password': pw_hash,
            'userType': form_data['userType']
        }).inserted_id
        response = ''
        if id == '':
            response = 'failed'
        else:
            response = 'success'
    else:
        response = 'failed'
    return render_template('signup.html', response=response)


@app.route('/login', methods=['GET', 'POST'])
@cross_origin()
def login():
    if request.method == 'POST':
        collection = db['users']
        form_data = request.form
        next_url = request.form.get('next')
        query_data = {
            "email": form_data['email']
        }
        result = collection.find_one(query_data)
        response = ''
        if result == None:
            response = 'failed'
        else:
            pw = form_data['password']
            if bcrypt.check_password_hash(result['password'], pw) == True:
                response = 'succeeded'
                session['email'] = form_data['email']
                session['name'] = result['name']
                session['userType'] = result['userType']
            else:
                response = 'failed'
        
        if response == 'failed':
            return render_template('login.html', response=response)
        else:
            if next_url:
                return redirect(next_url)
            else:
                return redirect(url_for('dashboard'))
    else:
        if "email" in session:
            return redirect(url_for("dashboard"))
        else:
            return render_template('login.html')

@app.route('/logout')
@cross_origin()
def logout():
    if 'email' in session:
        session.pop("email", None)
        session.pop("username", None)
        session.pop("userType", None)
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/resetdb')
@cross_origin()
def reset_database():
    collection1 = db['user_symptomps']
    collection2 = db['users']
    collection3 = db['messages']
    collection1.delete_many({})
    collection2.delete_many({})
    collection3.delete_many({})
    return "Database Cleared"

@app.route('/chat')
@cross_origin()
def chat():
    if "email" in session:
        messages = get_messages()
        return render_template('chat.html', username=session['name'], userType=session['userType'], messages=messages)
    else:
        return redirect(url_for('login', next='/chat'))


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent message to the room: {}".format(data['username'], data['message']))
    data['created_at'] = datetime.datetime.now().strftime("%d %b, %H:%M")
    save_message(data['message'], data['username'], data['userType'])
    socketio.emit('receive_message', data)


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room".format(data['username']))
    join_room(1)
    text = data['username'] + "(" + data['userType'] + ")" + " has joined the room"
    save_message(text, data['username'], data['userType'])
    socketio.emit('join_room_announcement', data)


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room".format(data['username']))
    leave_room(1)
    text = data['username'] + "(" + data['userType'] + ")" + " has left the room"
    save_message(text, data['username'], data['userType'])
    socketio.emit('leave_room_announcement', data)



import webhook


if __name__ == '__main__':
    socketio.run(app, debug=True)
