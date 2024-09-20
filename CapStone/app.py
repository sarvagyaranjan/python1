from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLite Configuration
# import os

# Get the absolute path to the current directory
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "users.db")}'


db = SQLAlchemy(app)

# Ensure uploads directory exists
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

# Create the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Hardcoded login
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid Credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    files = File.query.all()
    return render_template('dashboard.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)

    filename = secure_filename(file.filename)
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    
    new_file = File(filename=filename)
    db.session.add(new_file)
    db.session.commit()
    
    return redirect(url_for('dashboard'))

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    # Get the full path of the file to delete
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    # Check if the file exists before attempting to remove it
    if os.path.exists(file_path):
        try:
            os.remove(file_path)  # Remove the file from the filesystem

            # Remove the record from the database
            file_to_delete = File.query.filter_by(filename=filename).first()
            if file_to_delete:
                db.session.delete(file_to_delete)
                db.session.commit()
                flash('File deleted successfully.')
            else:
                flash('File record not found in the database.')
        except Exception as e:
            flash(f'Error occurred while deleting the file: {str(e)}')
    else:
        flash('File not found.')

    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
