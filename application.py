from flask import Flask, jsonify , make_response , request, render_template, redirect, url_for , send_from_directory
from flask_restful import Api
import os
from pymongo import MongoClient
from flask_cors import CORS  
from flask_jwt_extended import JWTManager
from flask_jwt_extended import (JWTManager, 
create_access_token, 
jwt_required, 
get_jwt_identity,
create_refresh_token,
get_jwt
)
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
from PIL import Image
import os
from common.constants import (
    JWT_ACCESS_TOKEN_TIMEDELTA,
    JWT_REFRESH_TOKEN_TIMEDELTA
)
import bcrypt

app = Flask(__name__)


app.config["MONGO_URI"] = os.environ.get("DATABASE_URL")
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'  # Change this to your secret key
app.config["JWT_SECRET_KEY"] = "super-secret" # Change this!

jwt = JWTManager(app)
CORS(app, origins=["http://localhost:3000"])

mongo_client = MongoClient(app.config["MONGO_URI"])
mongo = mongo_client["inspektlabs"]


# Configure rate limiting
limiter = Limiter(get_remote_address, app=app, default_limits=["5 per minute"])

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')



@app.route('/upload', methods=['POST'])
# @jwt_required(optional=False)
@limiter.limit("5 per minute")  # Rate limiting applied to this route
def upload():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return redirect(url_for('index'))

    file = request.files['file']

    # Check if the file has a name and is an allowed extension (e.g., JPEG or PNG)
    if file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('index'))

    # Securely save the uploaded file
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # Process the uploaded image
    image = Image.open(file_path)
    image_name = os.path.basename(file_path)
    file_name = file.filename
    return render_template('result.html', image_name=image_name , file_name = file_name)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'jpg', 'jpeg', 'png', 'gif'}



users_collection = mongo['users_collection']
# Create a JWT token for authentication
@app.route('/api/users', methods=['POST' , 'GET'])
def get_token():
    if request.method == 'GET':
        try:
            all_users_data = list(users_collection.find({}, {"_id": 0, "password": 0}))
            if all_users_data:
                        return all_users_data
        except Exception as e:
            return make_response(
                jsonify(
                    {
                        "message": "Something went wrong",
                        "Exception": str(e),
                    }
                ),
                500,
            )
    elif request.method == 'POST':
        try:
            data = request.json
            print(data)
            email = data["email"]
            password = data["password"].encode()
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(12))
            data["password"] = hashed_password
            mongo.users_collection.insert_one(data)

            #These tokens are to be handled by the front ent to be sent as cookies for protected routues
            access_token = create_access_token(
                identity=email, expires_delta=JWT_ACCESS_TOKEN_TIMEDELTA
            )

            #Create access token from refresh token in case its expired
            refresh_token = create_refresh_token(
                identity=email, expires_delta=JWT_REFRESH_TOKEN_TIMEDELTA
            )
            ret = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
            create_session(email, access_token, refresh_token)
            return make_response(
                jsonify(
                    {
                        "status": "Success",
                        "message": 'User created' , 
                        "data": ret,
                        "email" : data["email"]
                    }
                ),
                200,
            )
            
        except Exception as e:
            return make_response(
                jsonify(
                    {
                        "message": "Something went wrong",
                        "Exception": str(e),
                    }
                ),
                500,
            )

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data["email"]
        user = users_collection.find_one({"email": email})
        
        if user and bcrypt.checkpw(data["password"].encode(), user["password"]):
            access_token = create_access_token(
            identity=email, expires_delta=JWT_ACCESS_TOKEN_TIMEDELTA
        )

            #Create access token from refresh token in case its expired
            refresh_token = create_refresh_token(
                identity=email, expires_delta=JWT_REFRESH_TOKEN_TIMEDELTA
            )
            ret = {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }
            create_session(email, access_token, refresh_token)
            return make_response(
            jsonify(
                {
                    "status": "Success",
                    "message": 'User Login' , 
                    "data": ret,
                    "email" : data["email"]
                }
            ),
            200,
            )

            #Not working 
            # response.set_cookie("email", user["email"], expires=1000)  # Set the cookie to expire after 7 days
            # return {"message": "Login successful", "email": user["email"]}, 200
        else:
            return {"message": "Invalid credentials"}, 401
    except Exception as e:
        return make_response(
            jsonify({"message": "Something went wrong", "Exception": str(e)}), 500
        )

@app.route('/api/logout')
# @jwt_required(optional=False)
def logout():
    try:
        jti = get_jwt()['jti']
        if(not jti):
            return make_response(
                jsonify(
                        {
                            "status": "Api Failed",
                            "message": "Invalid Token",
                        }
                    ),
                    200,
                )

        blacklist_token(jti)
        return make_response(
                jsonify(
                    {
                        "status": "Success",
                        "message": "Logout Success",
                    }
                ),
                200,
            )
    except Exception as e:
        return make_response(
            jsonify(
                {
                    "status": "Api Failed",
                    "message": "Something went wrong",
                    "Exception": str(e),
                }
            ),
            500,
        )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/upload_captured', methods=['POST'])
# @jwt_required()
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




@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    val = is_jti_blacklisted(jti)
    return val

def is_jti_blacklisted(jti):
    try:
        response = mongo.blacklisted_tokens.find_one({'jti': jti})
        return bool(response)
    except Exception as e:
        print("Exception: ", str(e))



# user has an expired but otherwise valid access token in their request
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    return make_response(
        jsonify(
            {
                "status": "API_ERROR_STATUS",
                "message": "Your access token has expired. Please login again",
            }
        ),
        440,
    )


@jwt.invalid_token_loader  # user has an invalid access token in their request
def my_invalid_token_callback(jwt_header):
    return make_response(
        jsonify(
            {"status": "API_ERROR_STATUS", "message": "Your access token is invalid"}
        ),
        403,
    )


@jwt.unauthorized_loader  # user has no access token
def my_unauthorised_token_callback(jwt_header):
    return make_response(
        jsonify(
            {"status": "API_ERROR_STATUS", "message": "No access token found in request"}
        ),
        401,
    )


@jwt.revoked_token_loader  # user has a revoked access token in their request
def my_revoked_token_callback(jwt_header, jwt_payload):
    return make_response(
        jsonify(
            {
                "status": "API_ERROR_STATUS",
                "message": "You have logged out / logged in on another device.",
            }
        ),
        410,
    )

def create_session(email, access_token_jti, refresh_token_jti):
    try:
        result = mongo.sessions.insert_one({"email": email, 
        "access_token_jti": access_token_jti, "refresh_token_jti": refresh_token_jti})
    except Exception as e:
        print("Exception: ", str(e))

def blacklist_token(jti):
    try:
        mongo.backoffice_blacklist_tokens.update_one(
            {'jti': jti}, {'$set': {'jti': jti}},upsert=True)
    except Exception as e:
        print("Exception: ", str(e))


if __name__ == '__main__':
    app.run(debug=True, port=8000)
