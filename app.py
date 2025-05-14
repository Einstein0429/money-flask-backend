from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'money-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(10), default='pending')

@app.route('/api/submit_comment', methods=['POST'])
def submit_comment():
    data = request.get_json()
    name = data.get('name')
    content = data.get('content')
    if not name or not content:
        return jsonify({'error': '字段不能为空'}), 400
    comment = Comment(name=name, content=content)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': '提交成功，等待审核'})

@app.route('/api/get_comments')
def get_comments():
    comments = Comment.query.filter_by(status='approved').order_by(Comment.timestamp.desc()).all()
    return jsonify([
        {
            'name': c.name,
            'content': c.content,
            'timestamp': c.timestamp.strftime('%Y-%m-%d %H:%M')
        } for c in comments
    ])

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['admin'] = True
            return redirect(url_for('admin'))
        flash("用户名或密码错误")
    if not session.get('admin'):
        return render_template('login.html')
    comments = Comment.query.order_by(Comment.timestamp.desc()).all()
    return render_template('admin.html', comments=comments)

@app.route('/approve/<int:id>')
def approve(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    comment = Comment.query.get_or_404(id)
    comment.status = 'approved'
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/delete/<int:id>')
def delete(id):
    if not session.get('admin'):
        return redirect(url_for('admin'))
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
