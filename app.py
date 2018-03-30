from flask import Flask, render_template , request , flash , redirect , url_for , session , logging , request
from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField , TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
# flash for flash messaging

#create instance of flask class
app = Flask(__name__) #app is object

# Have to restart server again and again so use debug mode
#app.debug = True


#Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'toor'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)


#routing
@app.route('/')
def index():	#this is what shows on webpage
	return render_template('home.html')
	# return 'INDEX25152'
#normally dont return a string but a template

@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

#Articles = Articles()

@app.route('/articles')
def articles():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('articles.html',articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('articles.html',msg=msg)    
    #close connection
    cur.close()

#register form class
@app.route('/article/<string:id>/')
def article(id):
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])
    
    article = cur.fetchone()
    
    return render_template ('article.html',article=article) 

class RegisterForm(Form):
    name = StringField('Name',[validators.Length(min = 1 , max =50)])
    username = StringField('Username',[validators.Length(min=4,max=25)])
    email = StringField('Email',[validators.Length(min=6,max=50)])
    password = PasswordField('Password',[
            validators.DataRequired(),
            validators.EqualTo('confirm',message='Passwords do not match')    
        ])
    confirm = PasswordField('Confirm Password')

# user register
@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)    
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        #password = form.password.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create Cursor
        cur = mysql.connection.cursor()
        
        #Execute Cursor
        cur.execute("INSERT INTO users(name,email,username,password) VALUES (%s,%s,%s,%s)",(name,email,username,password))
        
        #Commit to DB
        mysql.connection.commit()

        #Close Connection
        cur.close()

        flash('You are now registered and can log in','success')
        return redirect(url_for('home'))

    return render_template('register.html', form = form)            

#user login

@app.route('/login',methods=['GET','POST'])
def login():
	if request.method == 'POST':
		#Get form fields
		username = request.form['username'] # different method than wtf
		password_candidate = request.form['password']

		#create cursor
		cur = mysql.connection.cursor()

		# get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s",[username])

		if result > 0:
			# get stored hash
			data = cur.fetchone() # get only first row
			password = data['password']	

			#compare passwords
			if sha256_crypt.verify(password_candidate,password):
			    #appe.logger.info('PASSWORD MATCHED')
			    session['logged_in'] = True
			    session['username'] = username
			    
			    flash('You are now logged in','success')
			    return redirect(url_for('dashboard'))		 		           
			else:
			    #app.logger.info('PASSWORD NOT MATCHED')
			    error = 'Invalid login'
			    return render_template('login.html',error=error)
		else:
			#app.logger.info('USERNAME NOT FOUND')
			error = 'USERNAME NOT FOUND'
			return render_template('login.html',error=error)
	return render_template('login.html')
# check if user logger_in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args,**kwargs)
        else: 
	    flash('Unauthorized,Please login','danger')
            return redirect(url_for('login'))
    return wrap	    

#logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out','success')
    return redirect(url_for('login'))

# cant see dashboard now when logout but can accesss... so to prevent use decorator

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    #Create cursor
    cur = mysql.connection.cursor()

    #Get articles
    result = cur.execute("SELECT * FROM articles")
    articles = cur.fetchall()
    if result > 0:
        return render_template('dashboard.html',articles=articles)
    else:
        msg = "No Articles Found"
        return render_template('dashboard.html',msg=msg)    
    #close connection
    cur.close()

#Article Form Class
class ArticleForm(Form):
    title = StringField('Title',[validators.Length(min = 1 , max =200)])
    body = TextAreaField('Body',[validators.Length(min=30)])
    
#Add Article
@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #Create cursor
        cur = mysql.connection.cursor()

        #Exexute
        cur.execute("INSERT INTO articles(title,body,author)VALUES(%s, %s, %s)",(title, body, session['username']))    

	    #Commit to DB
        mysql.connection.commit()

        #Close connectionn
        cur.close()

        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form = form)

#Edit Article
@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    # Create Cursor
    cur = mysql.connection.cursor()
    
    #Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s",[id])
    article = cur.fetchone()
    
    #Get form
    form = ArticleForm(request.form)
    
    #Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        #Create cursor
        cur = mysql.connection.cursor()

        #Exexute
        cur.execute("UPDATE articles SET title = %s, body = %s WHERE id = %s ",(title,body,id))

        #Commit to DB
        mysql.connection.commit()

        #Close connectionn
        cur.close()

        flash('Article Updated', 'success')
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html',form = form)        

#Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    #create cursor
    cur = mysql.connection.cursor()

    #execute
    cur.execute("DELETE FROM articles WHERE id = %s",[id])

    #Commit to DB
    mysql.connection.commit()

    #Close connectionn
    cur.close()

    flash('Article Deleted', 'success')
    return redirect(url_for('dashboard'))


#means script is going to be executed
if __name__ == '__main__' :
    app.secret_key = 'secret123'
    app.run(debug=True)
























def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

