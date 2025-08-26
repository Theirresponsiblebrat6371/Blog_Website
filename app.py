# Imports
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "Dracian"

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Database model for User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(150), nullable=False)
    role = db.Column(db.Integer, nullable=False, default=0) 

    blogs = db.relationship('Creator', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Creator(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    

# Routes
@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("Dashboard"))
    else:
        return render_template("index.html")



@app.route("/redirect_home", methods=["POST"])
def redirect_home():
    action = request.form.get("action")
    username = request.form.get("username")
    password = request.form.get("password")
    user = User.query.filter_by(username=username).first()
     
    if action == "Login":
        if user and user.check_password(password):
            session["username"] = username
            session["role"] = user.role
            return redirect(url_for("Dashboard"))
        else:
            return render_template("index.html", error="Invalid username or password")
        
    elif action == "Register":
        return redirect(url_for("register"))
    





@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role", 0, type=int)
        
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("Register.html", error="Username already exists")
        
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session["username"] = username
        session["role"] = new_user.role

        return redirect(url_for("Dashboard"))

    return render_template("Register.html")




@app.route("/Dashboard")
def Dashboard():

    if "username" not in session:
        return redirect(url_for("home"))
    role = session.get("role")
    if role == 1:
        blogs = Creator.query.all()
        if not blogs:
            return render_template("admin_dashboard.html", username=session["username"], message="No blogs published yet")
        return render_template("admin_dashboard.html", username=session["username"], blogs=blogs)
    else:
        return render_template("Dashboard.html", username=session["username"])



@app.route("/manage_blogs/<int:blog_id>")
def manage_blogs(blog_id):
    if "username" not in session:
        return redirect(url_for("home"))
    blog = Creator.query.get(blog_id)
    
    return render_template("manage.html", username=session["username"], blog=blog)


@app.route("/update/<int:id>", methods=['POST', 'GET'])
def update(id:int):
    Post_to_update = Creator.query.get_or_404(id)
    if request.method == "POST":
        Post_to_update.title = request.form['title']
        Post_to_update.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")
            return f"Error: {e}"
    else:
        return render_template('edit.html', blog=Post_to_update)

@app.route("/delete/<int:blog_id>")
def delete_blog(blog_id):
    Post_to_delete = Creator.query.get_or_404(blog_id)
    try:
        db.session.delete(Post_to_delete)
        db.session.commit()
        return redirect('/Dashboard')
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}"



@app.route("/create_blog", methods=["GET", "POST"])
def create_blog():
    if "username" not in session:
        return redirect(url_for("home"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        user_id = User.query.filter_by(username=session["username"]).first().id

        new_blog = Creator(title=title, content=content, user_id=user_id)
        db.session.add(new_blog)
        db.session.commit()

        return redirect(url_for("ExploreBlogs"))

    return render_template("CreateBlog.html", username=session["username"])



@app.route("/ExploreBlogs")
def ExploreBlogs():
    blogs = Creator.query.all()
    if blogs:
        return render_template("Explore.html", blogs=blogs)
    else:
        return render_template("Explore.html", message="No blogs available")



@app.route("/blog/<int:blog_id>")
def Article_view(blog_id):

    blog = Creator.query.get(blog_id)
    if blog:
        return render_template("article.html", blog=blog)
    return "Article not found", 404



# Logout
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("home"))


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)