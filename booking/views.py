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

from flask_jwt_extended import (
    get_jwt_identity,
    jwt_required , 
    get_jwt
)

class Register_Booking(Resource):
    def get(self):
        try:
            email = request.args.get("email", None)
            if email is None:
                return {"message": "email not found"}, 404
            user_bookings = list(bookings_collection.find({"email": email },{"_id":0}))
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
        
    @jwt_required(optional=False)
    def post(self):
        try:
            email =  get_jwt_identity()
            if email is None:
                return {"message": "email not found"}, 404
            flight_number = request.args.get("flight_number", None)
            if flight_number is None:
                return {"message": "flight_number not found"}, 404
            seats = request.args.get("seats", 1)
            
            
            # Check if the flight exists
            flight = flights_collection.find_one({"flight_number": flight_number})
            if not flight:
                return {"message": "Flight not found"}, 404
            print(flight['departure_time'])
            
            
            
            
            
            #Booking before 2 hours from departure of flight is allowed in case there are seats vacant
            #Uncomment below to add this feature
            # departure_time = dt.strptime(flight['departure_time'], "%Y-%m-%d %H:%M:%S")
            # current_time = dt.now()
            # if (departure_time - current_time) < timedelta(hours=2):
            #     return {"message": "Cannot book a ticket. Less than 2 hours remaining for flight's departure."}, 409

            # Check for availability (assuming default seat count is 60)
            if flight["seats"] < int(seats):
                return {"message": f"Flight has {flight['seats']} seats vacant. Cannot make a booking."}, 409

            
            result = book_seats( flight_number , int(seats) )
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
                'email': email,
                'flight_number': flight_number,
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