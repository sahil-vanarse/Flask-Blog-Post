from flask import *
from flask_mysqldb import MySQL
import MySQLdb.cursors
from flask_mail import Mail
import json
import re
from datetime import datetime

with open('config.json','r') as c :
	params=json.load(c)['params']

local_server=True

app=Flask(__name__)
app.secret_key = 'sahilvanarse'

app.config.update(
	MAIL_SERVER = 'smtp.gmail.com',
	MAIL_PORT = '465',
	MAIL_USE_SSL = True,
	MAIL_USERNAME = params['gmail-user'],
	MAIL_PASSWORD = params['gmail-password'],
)

mail=Mail(app)

if(local_server):
	app.config['MYSQL_HOST'] = params['local_host']
	app.config['MYSQL_USER'] = params['local_user']
	app.config['MYSQL_PASSWORD'] = params['local_password']
	app.config['MYSQL_DB'] = params['local_db']

else:
	app.config['MYSQL_HOST'] = params['prod_host']
	app.config['MYSQL_USER'] = params['prod_user']
	app.config['MYSQL_PASSWORD'] = params['prod_password']
	app.config['MYSQL_DB'] = params['prod_db']

mysql=MySQL(app)

date=datetime.now()

# for error page rendering
@app.route('/error')
def error():
	return render_template('error.html')

# for Home page rendering
@app.route('/')
def home():
	session['home']="home"
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT * FROM posts')
	posts = cursor.fetchall()[0:params['no_of_posts']]
	return render_template('index.html',params=params,posts=posts)

# for About page rendering
@app.route('/about')
def about():
	return render_template('about.html',params=params)

# to go for a particular slug
@app.route('/post/<string:post_slug>',methods=['GET','POST'])
def post_route(post_slug):
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT * FROM posts WHERE slug=%s',[post_slug])
	post = cursor.fetchone()
	return render_template('post.html',params=params,post=post)

# for dashboard page rendering
@app.route('/dashboard',methods=['POST','GET'])
def dashboard():
	if 'home' in session:
		session.pop('home',None)
	if 'user' in session and session['user'] == params['admin_user']:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM posts')
		posts = cursor.fetchall()
		return render_template('dashboard.html',params=params,posts=posts)

	if request.method=='POST':
		username = request.form['uname']
		userpass = request.form['pass']
		if username == params['admin_user'] and userpass == params['admin_password']:
			# set the session variable
			session['user'] = username
			cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
			cursor.execute('SELECT * FROM posts')
			posts = cursor.fetchall()
			return render_template('dashboard.html',params=params,posts=posts)
		else:
			return redirect(url_for('error'))
	else:
		return render_template('login.html',params=params)

# to edit and add new post
@app.route('/edit/<string:sno>',methods=['POST','GET'])
def edit(sno):
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	cursor.execute('SELECT * FROM posts where sno=%s',[sno])
	post = cursor.fetchone()
	if 'user' in session and session['user'] == params['admin_user']:
		if request.method=='POST':
			box_title=request.form['title']
			content=request.form['content']
			date=datetime.now()
			slug=request.form['slug']
			img_file=request.form['img_file']
			subtitle=request.form['subtitle']

			if sno=='0':
				cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
				cursor.execute('INSERT INTO posts values (NULL,%s,%s,%s,%s,%s,%s)', (box_title,content,[date],slug,img_file,subtitle))
				post = cursor.fetchall()
				mysql.connection.commit()
			else:
				cursor.execute('UPDATE posts SET title=%s, content=%s, date=%s, slug=%s, img_file=%s, subtitle=%s where sno=%s',(box_title, content, [date], slug, img_file, subtitle,sno,))
				mysql.connection.commit()
				return redirect('/dashboard')
	return render_template('edit.html',params=params,post=post)


@app.route('/delete/<string:sno>')
def delete(sno):
	if 'user' in session and session['user'] == params['admin_user']:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('DELETE FROM posts WHERE sno=%s',(sno,))
		mysql.connection.commit()
		return redirect('/dashboard')
	else:
		return redirect('/')



# contact page randering for user to add some comments and message
@app.route('/contact',methods=['POST','GET'])
def contact():
	if request.method=='POST':
		#Add entry to the database
		name = request.form['name']
		email = request.form['email']
		phone_num = request.form['phone_num']
		msg = request.form['msg']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('INSERT INTO contacts values (NULL,%s,%s,%s,%s,%s)', (name,email,phone_num,msg,[date]) )
		mysql.connection.commit()
		mail.send_message('New message from Blog', 
						   sender=email,
						   recipients=[params['gmail-user']],
						   body = name + "\n" +msg + "\n" +phone_num,
						   )
	return render_template('contact.html',params=params)

@app.route('/adminlogout')
def adminlogout():
	session.pop('user',None)
	return redirect('/')

if __name__=="__main__":
	app.Flaskrun(debug=True)