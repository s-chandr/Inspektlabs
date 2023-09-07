from application import api, mongo
from flask import Blueprint , jsonify, make_response , request
from flask_restful import Resource
import uuid
import time
import bcrypt
from common.extentions import jwt
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token
)
from common.constants import (
    JWT_ACCESS_TOKEN_TIMEDELTA,
    JWT_REFRESH_TOKEN_TIMEDELTA
)
from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required , 
    get_jwt
)
User = Blueprint("user", __name__)  # create Blueprint
users_collection = mongo['users_collection']



#Add user and get all user
class Register_User(Resource):
    def get(self):
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
    def post(self):
        try:
            data = request.json
            email = data["email"]
            password = data["password"].encode()
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt(12))
            data["password"] = hashed_password
            users_collection.insert_one(data)

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
class Update_User(Resource):
    # @jwt_required(optional=False) # commented out for testing purposes
    def get(self , email = None):
        try:
            
            if email:
                user_data = users_collection.find_one({"email": email}, {"_id": 0, "password": 0})

                if user_data:
                    return user_data
                else:
                    return make_response(jsonify({"message": "User not found"}), 404)
            
        except Exception as e:
            return make_response(jsonify({"message": "Something went wrong", "Exception": str(e)}), 500)
        
    
        
    def put(self, email=None):
        try:
            if email is None:
                return make_response(jsonify({"message": "email can not empty"}), 403)            
            data = request.json
            result = users_collection.update_one({'email': email}, {'$set': data})
            if result.modified_count > 0:
                return make_response(jsonify({'message': 'User updated'}), 200)
            else:
                return make_response(jsonify({'message': 'User not found'}), 404)
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
    def delete(self , email = None):
        try:
            result = users_collection.delete_one({'email': email})
            if result.deleted_count > 0:
                return make_response(jsonify({'message': 'User deleted'}), 200)
            else:
                return make_response(jsonify({'message': 'User not found'}), 404)
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
class Login(Resource):
    def post(self):
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

class Logout(Resource):
    @jwt_required(optional=False)
    def post(self):
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


api.add_resource(Update_User, "/users/<string:email>")
api.add_resource(Register_User , "/users")
api.add_resource(Login, "/login")
api.add_resource(Logout, "/logout")