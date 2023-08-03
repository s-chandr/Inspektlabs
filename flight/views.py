from application import api, mongo
from flask import Blueprint , jsonify, make_response , request
from flask_restful import Resource , reqparse
import uuid
import time
from datetime import datetime


Flight = Blueprint("flight", __name__)  # create Blueprint
flights_collection = mongo['flights_collection']



class Register_Flight(Resource):
    def get(self):
        flight_number = request.args.get("flight_number", None)
        if flight_number is None:
            return {"message": "Flight not found"}, 404    
        flight = flights_collection.find_one({"flight_number": flight_number} ,{'_id':0})
        
        if flight:
            return make_response(jsonify({"data":flight}), 200)
        return {"message": "Flight not found"}, 404
    
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('admin_id', type=str, required=True, help='admin_id  is required.')
        # parser.add_argument('flight_number', type=str, required=True, help='Flight number is required.')
        parser.add_argument('departure_time', type=lambda x: datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"), required=True, help='Flight departure time is required.')
        args = parser.parse_args()
        seats = 60
        flight = {
                'admin_id': args['admin_id'],
                'flight_number': str(uuid.uuid4().hex)[:10] + str(round(time.time())), #Random Flight Number
                'departure_time': str(args['departure_time']),
                'seats' : seats
            }
        result = flights_collection.insert_one(flight)
        inserted_id = str(result.inserted_id)
        flight['_id'] = inserted_id
        return jsonify(flight)
api.add_resource(Register_Flight, '/flight')