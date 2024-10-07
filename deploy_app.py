from flask import Flask, render_template
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/hogrider_db"
mongo = PyMongo(app)

@app.route('/<username>/<repository>')
def display(username, repository):
    repo = mongo.db.repositories.find_one({"owner": username, "name": repository})
    if repo:
        deploy_status = "成功"
        deploy_log = ["初始化...", "構建...", "部署中...", "完成!"]
        return render_template('deploy.html', repo=repo, status=deploy_status, log=deploy_log)
    else:
        return "儲存庫未找到", 404

if __name__ == '__main__':
    app.run(debug=True, port=5001,host='0.0.0.0')
