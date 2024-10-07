from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# 設置 Flask 配置
app.config['SECRET_KEY'] = 'your_secret_key'  # 更改為你的密鑰
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # 使用 SQLite 數據庫
app.config['UPLOAD_FOLDER'] = 'uploads'  # 設置上傳文件的文件夾
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳文件的大小

db = SQLAlchemy(app)

# 定義用戶模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# 定義儲存庫模型
class Repository(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    owner = db.Column(db.String(80), nullable=False)
    files = db.Column(db.PickleType, default=[])

# 創建數據庫
with app.app_context():
    db.create_all()

# 檢查文件擴展名
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

# 登入頁面
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['username'] = username
            flash('登入成功！', 'success')
            return redirect(url_for('home'))
        else:
            flash('無效的用戶名或密碼', 'error')
    
    return render_template('login.html')

# 註冊頁面
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            flash('用戶名已存在', 'error')
        else:
            hash_password = generate_password_hash(password)
            new_user = User(username=username, password=hash_password)
            db.session.add(new_user)
            db.session.commit()
            flash('註冊成功！請登入', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# 主頁面
@app.route('/')
def home():
    return render_template('home.html')

# 創建儲存庫
@app.route('/create_repository', methods=['GET', 'POST'])
def create_repository():
    if request.method == 'POST':
        repo_name = request.form['name']
        description = request.form['description']
        existing_repo = Repository.query.filter_by(name=repo_name, owner=session['username']).first()

        if existing_repo:
            flash('儲存庫名稱已存在', 'error')
            return redirect(url_for('create_repository'))

        new_repo = Repository(name=repo_name, description=description, owner=session['username'])
        db.session.add(new_repo)
        db.session.commit()
        flash('儲存庫創建成功', 'success')
        return redirect(url_for('home'))
    
    return render_template('create_repository.html')

# 顯示文件列表
@app.route('/repository/<username>/<repo_name>', methods=['GET', 'POST'])
def repository(username, repo_name):
    repo = Repository.query.filter_by(owner=username, name=repo_name).first()
    if not repo:
        flash('儲存庫不存在', 'error')
        return redirect(url_for('home'))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            repo.files.append(filename)
            db.session.commit()
            flash('文件上傳成功', 'success')
        else:
            flash('無效的文件類型', 'error')

    return render_template('files.html', files=repo.files, repo_name=repo_name)

# 下載文件
@app.route('/download/<repo_name>/<filename>')
def download_file(repo_name, filename):
    return redirect(url_for('static', filename=os.path.join(app.config['UPLOAD_FOLDER'], filename)))

# 登出
@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出！', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=10000, host='0.0.0.0')
