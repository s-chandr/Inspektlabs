from flask import Flask , Blueprint , request , jsonify
from flask_restful import Resource, Api, reqparse
import werkzeug
from application import api
import os

Upload = Blueprint("upload", __name__)  # create Blueprint


ALLOWED_EXTENSIONS = [ 'png', 'jpg', 'jpeg', 'gif']

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class UploadImage(Resource):
   def post(self):
        if 'file' not in request.files:		
            resp = jsonify({'message' : 'No file part in the request'})
            resp.status_code = 400
            return resp
        file = request.files['file']
        if file.filename == '':
            resp = jsonify({'message' : 'No file selected for uploading'})
            resp.status_code = 400
            return resp
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            file.save(os.path.join("/", file.filename))
            resp = jsonify({'message' : 'File successfully uploaded' , 'fileName' : file.filename})
            resp.status_code = 201
            return resp
        else:
            resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
            resp.status_code = 400
            return resp
     
    #  parse = reqparse.RequestParser()
    #  parse.add_argument('file', type=werkzeug.datastructures.FileStorage, location='files')
    #  args = parse.parse_args()
    #  image_file = args['file']
    #  image_file.save("your_file_name.jpg")

api.add_resource(UploadImage, "/upload")