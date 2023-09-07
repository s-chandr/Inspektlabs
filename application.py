# from flask import Flask, jsonify
# from flask_restful import Api
# import os
# from pymongo import MongoClient
# from flask_cors import CORS  
# from common.extentions import jwt
# from flask_jwt_extended import JWTManager

# app = Flask(__name__)


# app.config["MONGO_URI"] = os.environ.get("DATABASE_URL")

# #os.environ.get(Noth works)
# app.config["JWT_SECRET_KEY"] = "super-secret" # Change this!
# jwt = JWTManager(app)

# CORS(app, origins=["http://localhost:8000"])


# api = Api(app)
# mongo_client = MongoClient(app.config["MONGO_URI"])

# mongo = mongo_client["BiPolar"]

# # creating another flask app to handle /favicon.ico redirects and tracebacks
# ping_app = Flask(__name__)

# @ping_app.route('/', methods=['GET'])
# def ping():
#     return jsonify({'Ping Hello!': 'World!'})

from flask import Flask, request, render_template, redirect, url_for , send_from_directory
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'  # Change this to your secret key
jwt = JWTManager(app)

# Configure rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


# @app.route('/upload', methods=['POST'])

# @limiter.limit("5 per minute")  # Rate limiting applied to this route
# def upload():
#     # Check if a file was uploaded
#     if 'file' not in request.files:
#         return redirect(url_for('index'))

#     file = request.files['file']

#     # Check if the file has a name and is an allowed extension (e.g., JPEG or PNG)
#     if file.filename == '' or not allowed_file(file.filename):
#         return redirect(url_for('index'))

#     # Securely save the uploaded file
#     filename = secure_filename(file.filename)
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     file.save(file_path)

#     # Process the uploaded image
#     image = Image.open(file_path)
#     image_name = os.path.basename(file_path)
#     file_name = file.filename
#     return render_template('result.html', image_name=image_name , file_name = file_name)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}


# Create a JWT token for authentication
@app.route('/get_token', methods=['POST'])
def get_token():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    if username == 'your_username' and password == 'your_password':
        access_token = create_access_token(identity=username)
        return {'access_token': access_token}
    else:
        return {'message': 'Invalid credentials'}, 401

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/upload_captured', methods=['POST'])

@limiter.limit("5 per minute")
def upload_captured():
    file = request.files['file']

    if file.filename == '' or not allowed_file(file.filename):
        return {'message': 'Invalid file'}, 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    image_name = os.path.basename(file_path)
    return {'image_name': filename}


@app.route('/result')
def result():
    image_name = request.args.get('image_name', 'default.jpg')  # Default image name if not provided
    filename = secure_filename(image_name)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_name = os.path.basename(file_path)
    return render_template('result.html', image_name=image_name , file_name = filename)

if __name__ == '__main__':
    app.run(debug=True)
