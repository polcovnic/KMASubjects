from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from pyrogram import Client, filters

from models.subject import SubjectModel
from models.user import UserModel


class PhoneNumber(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('phone-number', type=str)

    @jwt_required()
    def post(self):
        app = Client('polcovnic', phone_number='+380957441355')
        print('telegram')
        with app:
            code = input('Enter code: ')
            app.phone_code = code
            user = app.get_users('self')
            original_text = 'message'
            message = app.send_message(user.id, original_text)
            message.delete()

        return {"message": "Sent request to get verification code"}, 201
