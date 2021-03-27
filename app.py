from flask import Flask, request, render_template, redirect, url_for, flash, session, request
from base64 import b64encode
from flask_sqlalchemy import SQLAlchemy
import os
import datetime
from random import randint  
app = Flask(__name__)
db = SQLAlchemy(app)

db_path = os.path.join(os.path.dirname(__file__), 'mydb.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SECRET_KEY'] = 'isthissasecret'




class ForumPost(db.Model):
	post_id=db.Column(db.Integer, primary_key=True)
	date_posted=db.Column(db.Date)
	category=db.Column(db.String)
	title = db.Column(db.String)
	content = db.Column(db.Text)
	user_posted = db.Column(db.String)
	latest_reply = db.Column(db.DateTime)



class Reply(db.Model):
	id  = db.Column(db.Integer, primary_key=True)
	post_id = db.Column(db.Integer)
	date_posted = db.Column(db.DateTime)
	category= db.Column(db.String)
	content = db.Column(db.Text)
	user_posted = db.Column(db.String)


class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	date_joined =db.Column(db.Date)
	username = db.Column(db.String)
	password = db.Column(db.String)


	
#fix forum home num thing
#session logged in on certain pages-  create post, edit post
#clean up, look pretty	
@app.route("/forumhome")
def forumhome():
	num_travel = len(ForumPost.query.filter_by(category='travel').all())
	num_gaming = len(ForumPost.query.filter_by(category='gaming').all())
	num_shopping = len(ForumPost.query.filter_by(category='shopping').all())
	num_sports = len(ForumPost.query.filter_by(category='sports').all())
	num_relationships = len(ForumPost.query.filter_by(category='relationships').all())
	return render_template("forumhome.html", user=session.get("user"), num_travel=num_travel, num_gaming=num_gaming, num_shopping=num_shopping, num_sports=num_sports, num_relationships=num_relationships)



@app.route("/category/<string:category>")
def viewcategory(category):

	all_posts = ForumPost.query.filter(ForumPost.category==category).order_by(ForumPost.latest_reply.desc()).all()
	#order posts by which one has the latest reply

	return render_template("viewcategory.html", category=category, all_posts=all_posts, user=session.get("user"))



@app.route("/me")

def me():
	if not session.get("user"):
		return redirect(url_for("login"))
	num_postings = len(ForumPost.query.filter_by(user_posted=session.get("user")).all())
	num_replies = len(Reply.query.filter_by(user_posted=session.get("user")).all())
	all_posts = ForumPost.query.filter_by(user_posted=session.get("user")).all()
	now = datetime.date.today()
	user = User.query.filter_by(username=session.get("user")).first()
	date_joined = user.date_joined
	days_since_joined = (now-date_joined).days
	return render_template("me.html", user=session.get("user"), num_postings=num_postings, num_replies=num_replies, all_posts=all_posts, days_since_joined=days_since_joined)


@app.route("/editpost/<int:id>", methods=['GET', 'POST'])
def editpost(id):
	if request.method == "POST":
		title = request.form['title']
		content = request.form['content']
		post_to_update = ForumPost.query.filter_by(post_id=id).first()
		if title == "" or content == "":
			flash("please make sure all fields are filled out.")
			return redirect(url_for('editpost', id=id))
		else:
			post_to_update.title = title
			post_to_update.content = content 
			db.session.commit()
			return redirect(url_for("me"))



	post_to_edit = ForumPost.query.filter_by(post_id=id).first()
	return render_template("editpost.html", user=session.get("user"), post_to_edit=post_to_edit)	


@app.route("/userprofile/<string:username>")
def userprofile(username):
	#if signed in user equals viewed username
	#redirect to 'me'
	if session.get("user") == username:
		return redirect(url_for("me"))
		#get the user's current number of postings
	num_postings = len(ForumPost.query.filter_by(user_posted=username).all())
	num_replies = len(Reply.query.filter_by(user_posted=username).all())
	all_posts = ForumPost.query.filter_by(user_posted=username).all()
	now = datetime.date.today()
	user = User.query.filter_by(username=username).first()
	date_joined = user.date_joined
	days_since_joined = (now-date_joined).days 
	return render_template("userprofile.html", user=session.get("user"), all_posts = all_posts, username=username, days_since_joined=days_since_joined, num_postings=num_postings, num_replies=num_replies)



@app.route("/createpost", methods=['GET', 'POST'])
def createpost():
	if request.method == "POST":
		post_id = randint(10000, 99999)
		category = request.form['category']
		title = request.form['title']
		content = request.form['content']
		if title == "" or content == "":
			flash("please make sure all fields are filled out.")
			return redirect(url_for("createpost"))
		else:
			user_posted = User.query.filter_by(username=session.get("user")).first().username 
			date_posted= datetime.date.today()
			new_post = ForumPost(post_id=post_id, category=category, title=title, content=content, user_posted=user_posted, date_posted=date_posted)
			db.session.add(new_post)
			db.session.commit()
			flash("your post has been added.")
			return redirect(url_for('viewcategory', category=category))
	return render_template("createpost.html", user=session.get("user"))



@app.route("/viewpost/<int:id>", methods=['GET', 'POST'])
def viewpost(id):
	if request.method == "POST":
		primary_id= randint(10000, 99999)
		post_id = id
		date_posted = datetime.datetime.now()
		category = ForumPost.query.filter_by(post_id=id).first().category
		content = request.form['content']
		user_posted = session.get("user")
		r = Reply(id=primary_id,post_id=post_id, date_posted=date_posted, category=category, content=content, user_posted=user_posted)
		post_to_update = ForumPost.query.filter_by(post_id=id).first()
		post_to_update.latest_reply = date_posted
		db.session.add(r)
		db.session.commit()
		return redirect(url_for("viewpost", id=id))
   


	#get the viewed post
	viewed_post = ForumPost.query.filter_by(post_id=id).first()
	#get all the replies associated with that post by date asc
	viewed_post_replies = Reply.query.filter_by(post_id=viewed_post.post_id).order_by(Reply.date_posted.asc())
	page = request.args.get("page", 1, type=int)
	viewed_post_replies = viewed_post_replies.paginate(per_page=2, page=page, error_out=True)
	return render_template("viewpost.html", viewed_post=viewed_post, viewed_post_replies=viewed_post_replies, user=session.get("user"))



@app.route("/register", methods=['GET', 'POST'])
def register():
	if request.method == "POST":
		errors = []
		username = request.form['username']
		usernametwo=  request.form['usernametwo']
		password= request.form['password']
		if username!=usernametwo:
			errors.append("please make sure usernames match.")
		if len(str(username)) < 6 or len(str(password)) < 6:
			errors.append("please make sure your username and password are at least six characters.")
		#check that username isn't in use
		user_exists = bool(User.query.filter_by(username=username).first())
		if user_exists is True:
			errors.append("your username is already in use.")
		if errors:
			for error in errors:
				flash(error)
			return redirect(url_for("register"))
		else:
			rand_id = randint(10000, 99999)
			new_user = User(user_id = rand_id, date_joined=datetime.date.today(), username=request.form['username'], password = request.form['password'])
			db.session.add(new_user)
			#start session
			session['user'] = request.form['username']
			db.session.commit()
			return redirect(url_for("forumhome"))
	return render_template("register.html", user=session.get("user"))

@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("forumhome"))

@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		username = request.form['username']
		password = request.form['password']
		does_user_exist = len(User.query.filter_by(username=username, password=password).all())
		if does_user_exist == 0:
			flash("your username and/or password is incorrect.")
			return redirect(url_for("login"))
		else:
			#log the user in
			session['user'] = username
			return redirect(url_for("forumhome"))
	return render_template("login.html", user=session.get("user"))




