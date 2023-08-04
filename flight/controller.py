from application import  mongo
flights_collection = mongo['flights_collection']

def book_seats( flight_number , taken ) :
    result = flights_collection.update_one(
        {"flight_number": flight_number},
        {"$inc": {"seats": -taken}}
    )
    return True if result.modified_count == 1 else False