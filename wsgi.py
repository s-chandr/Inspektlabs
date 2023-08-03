from werkzeug import run_simple
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.exceptions import NotFound
from application import app,ping_app
from user.views import User
from flight.views import Flight
from booking.views import Booking


app.register_blueprint(User)
app.register_blueprint(Flight)
app.register_blueprint(Booking)

application = DispatcherMiddleware(ping_app, {"/indigos": app})

if __name__ == "__main__":
    run_simple("0.0.0.0", 8000, application, use_reloader=True, threaded=True)
