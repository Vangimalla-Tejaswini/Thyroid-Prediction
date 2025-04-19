from flask import Flask,render_template,redirect,request,url_for, send_file
import mysql.connector, joblib
import pandas as pd
import numpy as np


app = Flask(__name__)
app.secret_key = 'thyroid' 

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='thyroid'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        if password == c_password:
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = []
            for i in email_data:
                email_data_list.append(i[0])
            if email.upper() not in email_data_list:
                query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
                values = (name, email, password)
                executionquery(query, values)
                return render_template('login.html', message="Successfully Registered!")
            return render_template('register.html', message="This email ID is already exists!")
        return render_template('register.html', message="Conform password is not match!")
    return render_template('register.html')


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        query = "SELECT UPPER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = []
        for i in email_data:
            email_data_list.append(i[0])

        if email.upper() in email_data_list:
            query = "SELECT UPPER(password) FROM users WHERE email = %s"
            values = (email,)
            password__data = retrivequery1(query, values)
            if password.upper() == password__data[0][0]:
                global user_email
                user_email = email

                return redirect("/home")
            return render_template('login.html', message= "Invalid Password!!")
        return render_template('login.html', message= "This email ID does not exist!")
    return render_template('login.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/upload', methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files['file']
        df = pd.read_csv(file)
        df1 = df.head(500)
        
        # Render the data as an HTML table with Bootstrap classes for styling
        return render_template('view.html', 
                               data=df1.to_html(classes='table table-striped table-bordered table-hover', index=False), 
                               message="Dataset uploaded successfully! Go to Splitting!")
    return render_template('upload.html')


@app.route('/split', methods=["GET", "POST"])
def split():
    if request.method == "POST":
        return render_template('prediction.html', message="Model trined successfully! Go for prediction!")
    return render_template('split.html')



### Prediction Part

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'POST':
        tumor = int(request.form['tumor'])
        TSH_measured = int(request.form['TSH_measured'])
        pregnant = int(request.form['pregnant'])
        on_antithyroid_meds = int(request.form['on_antithyroid_meds'])
        query_hyperthyroid = int(request.form['query_hyperthyroid'])
        query_hypothyroid = int(request.form['query_hypothyroid'])
        TT4 = float(request.form['TT4'])
        FTI = float(request.form['FTI'])
        TSH = float(request.form['TSH'])
        T4U = float(request.form['T4U'])

        # Load the saved model
        model = joblib.load('MODELS/best_ensemble_model.pkl')

        # Define class mappings
        condition_class = {
            0: "Subclinical (initial level)", 
            1: "T3 toxic", 
            2: "toxic goitre", 
            3: "secondary toxic", 
            4: "Subclinical (initial level)",
            5: "primary hypothyroid",
            6: "compensated hypothyroid",
            7: "secondary hypothyroid",
        }

        disorder_class = {
            0: "hyperthyroid", 
            1: "hyperthyroid", 
            2: "hyperthyroid", 
            3: "hyperthyroid", 
            4: "hypothyroid",
            5: "hypothyroid",
            6: "hypothyroid",
            7: "hypothyroid",
        }

        # Prediction Function
        def prediction_func(input_features):
            input_array = np.array([input_features])
            print(input_array)
            
            # Make prediction
            prediction = model.predict(input_array)
            print(prediction)

            # Map the class label to disorder and condition
            predicted_disorder = disorder_class[prediction[0]]
            predicted_condition = condition_class[prediction[0]]
            
            return predicted_disorder, predicted_condition
        
        # predicted_disorder, predicted_condition = prediction_func([78.000000, 0, 85.000000, 1, 0, 23.000000, 0, 0.920000, 0, 0])
        predicted_disorder, predicted_condition = prediction_func([TT4, tumor, FTI, TSH_measured, pregnant, TSH, query_hyperthyroid, T4U, on_antithyroid_meds, query_hypothyroid])

        return render_template('prediction.html', predicted_disorder = predicted_disorder, predicted_condition = predicted_condition)
    return render_template('prediction.html')



if __name__ == '__main__':
    app.run(debug = True)