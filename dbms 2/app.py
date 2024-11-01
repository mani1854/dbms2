from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'secretkey123'  

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:manichaitra@localhost/use2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users1'  # Change the table name to user1
    username = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    fullname = db.Column(db.String(100))
    createdat = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Post(db.Model):
    postid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    src = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(255))
    caption = db.Column(db.Text)
    like_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    fk_username = db.Column(db.String(50), db.ForeignKey('users1.username'))  # Reference to user1
    view_count = db.Column(db.Integer, default=0)
    category = db.Column(db.String(50))

class Comment(db.Model):
    commentid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    comment_content = db.Column(db.Text, nullable=False)
    fk_username = db.Column(db.String(50), db.ForeignKey('users1.username'))  # Reference to user1
    postid = db.Column(db.Integer, db.ForeignKey('post.postid'))
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

class Like(db.Model):
    likeid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fk_postid = db.Column(db.Integer, db.ForeignKey('post.postid'))
    fk_username = db.Column(db.String(50), db.ForeignKey('users1.username'))  # Reference to user1

class Bookmark(db.Model):
    bookmarkid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fk_username = db.Column(db.String(50), db.ForeignKey('users1.username'))  # Reference to user1
    fk_postid = db.Column(db.Integer, db.ForeignKey('post.postid'))

class Report(db.Model):
    reportcount = db.Column(db.Integer, default=1)
    reason = db.Column(db.String(255))
    fk_username = db.Column(db.String(50), db.ForeignKey('users1.username'))  # Reference to user1
    fk_postid = db.Column(db.Integer, db.ForeignKey('post.postid'))
    __table_args__ = (db.PrimaryKeyConstraint(fk_username, fk_postid),)

@app.route('/')
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['username'] = user.username
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Login failed. Check your credentials.", "danger")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/post/<int:postid>', methods=['GET', 'POST'])
def post_detail(postid):
    post = Post.query.get_or_404(postid)
    if request.method == 'POST':
        comment_content = request.form['comment_content']
        new_comment = Comment(fk_username=session.get('username'), postid=postid, comment_content=comment_content)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('post_detail', postid=postid))

    comments = Comment.query.filter_by(postid=postid).all()
    return render_template('post_detail.html', post=post, comments=comments)

@app.route('/like/<int:postid>')
def like(postid):
    post = Post.query.get(postid)
    if post:
        post.like_count += 1
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/bookmark/<int:postid>')
def bookmark(postid):
    if 'username' in session:
        new_bookmark = Bookmark(fk_username=session['username'], fk_postid=postid)
        db.session.add(new_bookmark)
        db.session.commit()
    return redirect(url_for('home'))

@app.route('/bookmarks')
def bookmarks():
    if 'username' in session:
        bookmarks = Bookmark.query.filter_by(fk_username=session['username']).all()
        posts = [Post.query.get(b.fk_postid) for b in bookmarks]
        return render_template('bookmarks.html', posts=posts)
    return redirect(url_for('login'))

@app.route('/report/<int:postid>', methods=['POST'])
def report(postid):
    reason = request.form['reason']
    new_report = Report(fk_username=session['username'], fk_postid=postid, reason=reason)
    db.session.add(new_report)
    db.session.commit()
    return redirect(url_for('post_detail', postid=postid))

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():  
        db.create_all()  
    app.run(debug=True)
