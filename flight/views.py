from application import api, mongo
from flask import Blueprint , jsonify, make_response , request
from flask_restful import Resource , reqparse
import uuid
import time
from datetime import datetime
from flask_jwt_extended import (
    
    get_jwt_identity,
    jwt_required,
    
)

Flight = Blueprint("flight", __name__)  # create Blueprint
flights_collection = mongo['flights_collection']
users_collection = mongo['users_collection']



class Register_Flight(Resource):
    def get(self):
        try:
            flight_number = request.args.get("flight_number", None)
            if flight_number is None:
                flight = list(flights_collection.find({} ,{'_id':0}))
                return make_response(jsonify(flight), 200)   
            
            flight = flights_collection.find_one({"flight_number": flight_number} ,{'_id':0})
            if flight:
                return make_response(jsonify(flight), 200)
            return {"message": "Flight not found"}, 404
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
    @jwt_required(optional=False)
    def post(self):
        try:
            email = get_jwt_identity()
            result = users_collection.find_one({"username": email , "role" : "admin"},{'_id': 0})

            if result is None:
                return {"message": "Unauthorized access"}, 400
            
            parser = reqparse.RequestParser()
            parser.add_argument('admin_email', type=str, required=True, help='admin_email  is required.')
            parser.add_argument('departure_time', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"), required=True, help='Flight departure time is required.')
            args = parser.parse_args()
            seats = 60
            flight = {
                    'admin_email': args['admin_email'],
                    'flight_number': str(uuid.uuid4().hex)[:10] + str(round(time.time())), #Random Flight Number
                    'departure_time': str(args['departure_time']),
                    'seats' : seats
                }
            result = flights_collection.insert_one(flight)
            inserted_id = str(result.inserted_id)
            flight['_id'] = inserted_id
            return jsonify(flight)
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
        
    @jwt_required(optional=False)
    def delete(self):
        try:
            flight_number = request.args.get("flight_number", None)
            if flight_number is None:
                return {"message": "Flight number not provided in query parameters"}, 400

            # Check if the flight with the provided flight_number exists in the database
            flight = flights_collection.find_one({"flight_number": flight_number}, {'_id': 0})
            if flight:
                # If the flight exists, delete it
                delete_result = flights_collection.delete_one({"flight_number": flight_number})
                if delete_result.deleted_count == 1:
                    return {"message": f"Flight with flight_number '{flight_number}' has been deleted"}, 200
                else:
                    return {"message": "An error occurred while deleting the flight"}, 500
            else:
                return {"message": "Flight not found"}, 404
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
api.add_resource(Register_Flight, '/flight')