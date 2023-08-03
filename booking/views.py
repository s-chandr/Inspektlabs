from application import api, mongo
from flask import Blueprint , jsonify, make_response , request
from flask_restful import Resource , reqparse
import uuid
import time
from datetime import datetime as dt , timedelta 
from flight.controller import book_seats
Booking = Blueprint("booking", __name__)  # create Blueprint
bookings_collection = mongo['bookings_collection']
flights_collection = mongo['flights_collection']



class Register_Booking(Resource):
    def get(self):
        try:
            user_id = request.args.get("user_id", None)
            if user_id is None:
                return {"message": "user_id not found"}, 404
            user_bookings = list(bookings_collection.find({"user_id": user_id}))
            return make_response(jsonify({"data":user_bookings}), 200)
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
        
    #Booking before 2 hours from departure of flight is allowed in case there are seats vacant
    def post(self):
        try:
            user_id = request.args.get("user_id", None)
            if user_id is None:
                return {"message": "user_id not found"}, 404
            parser = reqparse.RequestParser()
            parser.add_argument('flight_number', type=str, required=True, help='Flight number is required.')
            parser.add_argument('seats', type=int, required=False, help='Seat Count is default 1')            
            args = parser.parse_args()

            # Check if the flight exists
            flight = flights_collection.find_one({"flight_number": args['flight_number']})
            if not flight:
                return {"message": "Flight not found"}, 404
            print(flight['departure_time'])
            departure_time = dt.strptime(flight['departure_time'], "%Y-%m-%d %H:%M:%S")
            current_time = dt.now()
            if (departure_time - current_time) < timedelta(hours=2):
                return {"message": "Cannot book a ticket. Less than 2 hours remaining for departure."}, 409

            # Check for availability (assuming default seat count is 60)
            if int(flight["seats"]) < int(args['seats']):
                return {"message": f"Flight has {flight['seats']} seats vacant. Cannot make a booking."}, 409

            
            result = book_seats( args["flight_number"] , args["seats"] )
            if not result:
                return make_response(
                jsonify(
                    {
                        "message": "Booking Unsuccessfull",
                    }
                ),
                500,
            )
            booking = {
                'user_id': user_id,
                'flight_number': args['flight_number'],
                'booking_time': dt.now()
            }
            result = bookings_collection.insert_one(booking)
            if not result.acknowledged:
                return make_response(
                jsonify(
                    {
                        "message": "Booking Unsuccessfull",
                    }
                ),
                500,
            )
            inserted_id = str(result.inserted_id)
            booking['_id'] = inserted_id
            return jsonify(booking)
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

api.add_resource(Register_Booking, '/booking')