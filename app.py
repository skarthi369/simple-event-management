from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, timedelta
import threading
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
app.config['MAIL_SERVER'] = 'smtp.example.com'  # Replace with your SMTP server
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@example.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'your_password'  # Replace with your email password

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('events', lazy=True))

def send_reminder(event):
    with app.app_context():
        msg = Message(f"Reminder: {event.title}", 
                      sender=app.config['MAIL_USERNAME'], 
                      recipients=[event.user.email])
        msg.body = f"Dear {event.user.name},\n\nThis is a reminder for your event: {event.title} on {event.date}."
        mail.send(msg)

def schedule_reminders():
    while True:
        now = datetime.utcnow()
        events = Event.query.filter(Event.date > now, Event.date < now + timedelta(days=1)).all()
        for event in events:
            reminder_time = event.date - timedelta(hours=1)
            delay = (reminder_time - now).total_seconds()
            threading.Timer(delay, send_reminder, args=[event]).start()
        time.sleep(3600)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/create_event', methods=['POST'])
def create_event():
    title = request.form['title']
    date = request.form['date']
    user_id = request.form['user_id']
    event = Event(title=title, date=datetime.strptime(date, '%Y-%m-%dT%H:%M'), user_id=user_id)
    db.session.add(event)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    threading.Thread(target=schedule_reminders).start()
    app.run(debug=True)
