from werkzeug.security import safe_str_cmp


from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    get_jti)

from flask_restful import Resource, reqparse
from models.user import UserModel
from blacklist import BLACKLIST


class UserRegister(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )

    def post(self):
        data = UserRegister.parser.parse_args()

        if UserModel.find_by_username(data['username']):
            return {"message": "A user with that username already exists"}, 400

        user = UserModel(data['username'], data['password'])
        user.save_to_db()
        user.save_cookies()

        return {"message": "User created successfully."}, 201


class User(Resource):
    @classmethod
    @jwt_required()
    def get(cls):
        # claims = get_jwt()
        # _id = claims['_id']
        user = UserModel.find_by_id(get_jwt_identity())

        if not user:
            return {'message': 'User not found'}
        return user.json()

    @classmethod
    def delete(cls, user_id):
        user = UserModel.find_by_id(user_id)
        if not user:
            return {'message': 'User not foud'}, 404
        user.delete_from_db()  # TODO
        return {'message': 'User deleted'}, 200


class UserLogin(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('username',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )
    parser.add_argument('password',
                        type=str,
                        required=True,
                        help="This field cannot be blank."
                        )


    @classmethod
    def post(cls):
        data = cls.parser.parse_args()

        user = UserModel.find_by_username(data['username'])

        if user and safe_str_cmp(user.password, data['password']):
            access_token = create_access_token(identity=user.id, fresh=True)
            refresh_token = create_refresh_token(user.id)
            return {
                       'access_token': access_token,
                       'refresh_token': refresh_token
                   }, 200
        return {'message': 'Invalid credentials'}, 401


class JWTGet(Resource):
    @jwt_required(optional=True)
    def get(self):
        user_id = get_jwt_identity()
        if user_id:
            return {"status": "active"}
        else:
            return {"status": "inactive"}


class UserLogout(Resource):
    @jwt_required()
    def post(self):
        BLACKLIST.add(get_jwt()['jti'])
        return {'message': 'Successfully logged out'}


class TokenRefresh(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        new_token = create_access_token(identity=current_user, fresh=False)
        return {'access_token': new_token}, 200