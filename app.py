from flask import Flask, render_template, request, url_for, flash,redirect,send_file,session
import pickle as pk
import os
import requests
import array as arr
import smtplib
import ssl
from email.message import EmailMessage
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from training import MLModel


# Define Email sender and receiver
email_sender = 'aksocredit@gmail.com'
email_password = 'wbjtoxznwxnhqdns'
email_receiver = 'akbaralishaik06@gmail.com'
# password = 'wbjtoxznwxnhqdns'


app = Flask(__name__, static_url_path='/static')
app.secret_key = 'Another secret key to crack!!'

#Database configure for SQL Alchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#User class for database creation
class user(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    email = db.Column(db.String(120))
    password = db.Column(db.String(80))

with app.app_context():
    db.create_all()

# #Opening the pickled file
# file = open('model.pkl', 'rb')
# result = pk.load(file)
# file.close()


#Route for accepting the file for detection
@app.route('/detectFile/<filename>',methods = ['POST'])
def detectFile(filename):
    if request.method == 'POST':
        session['filename'] = filename
        return redirect(url_for('prediction'))

# Route for detection
@app.route('/prediction',methods=['GET','POST'])
def prediction():
    filename = session.get('filename')
    model = MLModel(filename)
    model.create_model()

    
    #Opening the pickled file
    file = open('model.pkl', 'rb')
    result = pk.load(file)
    file.close()

    columns = result[1]
    if request.method == 'POST':
        Input = request.form
        inputs = arr.array('d', map(float, Input.values()))

        test = result[0].predict([inputs])
        test = 1
        if (test == 0):
            inp = dict(zip(list(columns), list(inputs)))
            return render_template('show.html', str1='Not Fraudulent', inp =inp)
        else:
            req = requests.get('https://ipinfo.io?token=973a2786b40e55')
            data = req.json()
            subject = 'Credit card Fraud detected!!!'
            body = f'''
                    TRANSACTIONAL DETAILS
                    

                    Stats Detected as: 
                    IP-Address : {data['ip']}
                    City       : {data['city']}
                    Location(Lat,Long) : {data['loc']}
                    Registered ISP : {data['org']}
                    Postal Code : {data['postal']}


                    Inputs:
                    Features : {list(columns)}
                    Input Values : {list(inputs)}
                '''
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)

            # Add SSL
            context = ssl.create_default_context()

            # Log in and send the email
            with smtplib.SMTP_SSL('smtp.gmail.com',465,context=context) as smtp:
                smtp.login(email_sender,email_password)
                smtp.sendmail(email_sender,email_receiver,em.as_string())

            print('Email sent Successfully')
            # msg = Message(f'The Transaction is found to be fraudulent.\n Input Parameters are {Input} \n User Location is {request.remote_addr}',sender ='shaikakbara77@gmail.com')
            # mail.send(msg)
            flash('Email sent to the concerned bank', Warning)
            inp = dict(zip(list(columns), list(inputs)))
            return render_template('show.html', str2='Fraudulent', inp=inp)
    return render_template('detection.html',columns=columns,collen=len(columns))


#Route for Home for All the Users
@app.route('/')
def index():
    return render_template('homeForNonUsers.html')

#Route for home for Logged Users Only
@app.route('/home', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


#Route for uploading a new file
@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        uploaded_file_name = request.form['fileName']
        uploaded_file.save(uploaded_file.filename)
        flash(f' The file {uploaded_file_name} is uploaded to the server successfully\nGo to admin page to access all the functionalities over the file.')
        return redirect('/home')
    else:
        return render_template('uploadFile.html')

#Route for Register or Sign Up
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        pass1 = request.form['password']
        pass2 = request.form['confirm_password']
        if pass1 != pass2:
            flash('Passwords are not matching', category='warning')
            return redirect('/register')
        else:
            register = user(username = username,email = email,password = pass1)
            db.session.add(register)
            db.session.commit()
            flash('User Registered Successfully',category='warning')
            return redirect('/login')
    return render_template('register.html')


#Route for Login or Sign In
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        key = request.form['password']

        login=user.query.filter_by(email = email,password = key).first()
        if login is not None:
            print(f'Login Variable: {login} ')
            flash('User Logged in successfully',category='Warning')
            return redirect('/home')
        else:
            flash('Invalid Password or Email')
            return redirect('/login')
    return render_template('login.html')

# Route for administration
@app.route('/admin',methods =['GET','POST'])
def admin():
     # Count the number of files in the directory where files are being uploaded
    num_files = len([name for name in os.listdir('.') if os.path.isfile(name)])

    # Get the list of all files in the directory where files are being uploaded with .csv extension
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    print(f'Number of files at root directory are {num_files} and csv files are {csv_files}')
    return render_template('admin.html',files = csv_files)

# Route for deletion of the file 
@app.route('/deletedata/<filename>',methods = ['GET','POST'])
def deletedata(filename):
    if request.method =='POST':
        try:
            os.remove(filename)
            flash(f'The file {filename}  is successfully deleted from the server')
            return redirect('/admin')
        except Exception as e:
            flash(f'Error Deleting the file : {str(e)}')
            return redirect('/admin')

#Route for Viewing the data of the file
@app.route('/viewdata/<filename>',methods = ['GET','POST'])
def viewdata(filename):
    if request.method == 'POST':
        df = pd.read_csv(filename)
        return render_template('viewdata.html',data = df.head(10).to_html(),file_name = filename)
    else:
        flash(f'The file {filename} does not exist on the server','error')
        return redirect('/admin')


# Route for Viewing a certain file
@app.route('/analysis/<filename>',methods = ['GET','POST'])
def analysis(filename):
    if request.method == 'POST':
        df = pd.read_csv(filename)
        return render_template('analysis.html', tps=df.dtypes, corners=df.shape, columns=df.columns, nullvalues=df.isnull().sum(), FraudCases=(df.iloc[:, -1] == 1).sum(), NFraud=(df.iloc[:, -1] == 0).sum(),filename = filename)
    return render_template('analysis.html')

if __name__ == '__main__':
    app.run(port=8000)
