from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_pymongo import PyMongo
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config["MONGO_URI"] = "mongodb://localhost:27017/hogrider_db"
mongo = PyMongo(app)

app.config['UPLOAD_FOLDER'] = './uploads'
app.config['ALLOWED_EXTENSIONS'] = {'py', 'txt', 'md', 'html', 'js', 'css'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = mongo.db.users.find_one({"username": username})
        
        if existing_user:
            flash('用戶名已被使用', 'error')
            return redirect(url_for('register'))
        
        mongo.db.users.insert_one({"username": username, "password": password})
        flash('註冊成功，請登入', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = mongo.db.users.find_one({"username": username})
        
        if user and user['password'] == password:
            session['username'] = user['username']
            flash('登入成功', 'success')
            return redirect(url_for('home'))
        else:
            flash('登入失敗，請檢查帳號密碼', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('登出成功', 'info')
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'username' in session:
        repositories = mongo.db.repositories.find({"owner": session['username']})
        return render_template('home.html', repositories=repositories)
    else:
        flash('請先登入', 'warning')
        return redirect(url_for('login'))

@app.route('/create_repository', methods=['GET', 'POST'])
def create_repository():
    if request.method == 'POST':
        repo_name = request.form['name']
        description = request.form['description']
        existing_repo = mongo.db.repositories.find_one({"name": repo_name, "owner": session['username']})
        
        if existing_repo:
            flash('儲存庫名稱已存在', 'error')
            return redirect(url_for('create_repository'))

        new_repo = {
            "name": repo_name,
            "description": description,
            "owner": session['username'],
            "files": []
        }
        mongo.db.repositories.insert_one(new_repo)
        flash('儲存庫創建成功', 'success')
        return redirect(url_for('home'))
    
    return render_template('create_repository.html')

@app.route('/repository/<username>/<repo_name>', methods=['GET', 'POST'])
def repository(username, repo_name):
    repo = mongo.db.repositories.find_one({"owner": username, "name": repo_name})
    if not repo:
        flash('儲存庫不存在', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            mongo.db.repositories.update_one({"_id": repo['_id']}, {"$push": {"files": filename}})
            flash('文件上傳成功', 'success')
        else:
            flash('無效的文件類型', 'error')

    return render_template('repository.html', repository=repo)

@app.route('/files/<repo_name>')
def files(repo_name):
    repo = mongo.db.repositories.find_one({"name": repo_name, "owner": session['username']})
    if repo:
        return render_template('files.html', files=repo['files'], repo_name=repo_name)
    else:
        flash('未找到儲存庫', 'error')
        return redirect(url_for('home'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000,host='0.0.0.0')
