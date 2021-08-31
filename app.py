from flask import Flask, jsonify
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS, cross_origin

from resources.user import UserRegister, User, UserLogin, TokenRefresh, UserLogout, JWTGet
from resources.subject import Subject, SubjectName
from resources.group import Group
from db import db
from blacklist import BLACKLIST

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PROPAGATE_EXCEPTIONS'] = True
app.config['JWT_BLACKLIST_ENABLED'] = True
app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access', 'refresh']
app.secret_key = 'jose'
api = Api(app)

CORS(app)


@app.before_first_request
def create_tables():
    db.create_all()


api.add_resource(UserRegister, '/register')  # private
api.add_resource(User, '/user')
api.add_resource(UserLogin, '/login')
api.add_resource(TokenRefresh, '/refresh')
api.add_resource(UserLogout, '/logout')
api.add_resource(JWTGet, '/jwt')
api.add_resource(Subject, '/subjects')
api.add_resource(Group, '/groups')
# api.add_resource(Subject, '/subject')
api.init_app(app)

jwt = JWTManager(app)


@jwt.additional_claims_loader
def add_claims_loader(identity):
    return {'_id': True}


@jwt.token_in_blocklist_loader
def check_id_token_in_blacklist(jwt_header, jwt_payload):
    return jwt_payload['jti'] in BLACKLIST


@jwt.expired_token_loader
def expired_token_callback(arg1, arg2):
    return jsonify({
        'description': 'The token has expired.',
        'error': 'token_expired'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(arg):
    return jsonify({
        'description': 'What the fuck are you doing???',
        'error': 'invalid_token'
    }), 401


@jwt.unauthorized_loader
def unauthorized_callback(arg):
    return jsonify({
        'description': 'You need to send JWT token',
        'error': 'unauthorized'
    }), 401


@jwt.needs_fresh_token_loader
def token_not_fresh_callback():
    return jsonify({
        'description': 'Fresh token needed',
        'error': 'fresh_token_required'
    }), 401


@jwt.revoked_token_loader
def revoked_token_callback(arg1, arg2):
    return jsonify({
        'description': 'Token is no longer valid (you have logged out)',
        'error': 'revoked_token'
    }), 401


if __name__ == '__main__':
    db.init_app(app)
    app.run(port=5000, debug=True)
