import re

from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from flask_cors import cross_origin

from models.group import GroupModel
from models.user import UserModel
from saz_signuper.group_signuper import GroupSignuper
from saz_signuper import telegram


class Group(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('groups', type=dict)

    @jwt_required()
    @cross_origin()
    def post(self):
        try:
            data = self.parser.parse_args()['groups']
            body = data['body']
            date = data['date']
            name = data['name']
            user_id = get_jwt_identity()
            user: UserModel = UserModel.find_by_id(user_id)
            user.groups_date = date
            groups = dict()
            for group in body:
                group_id = re.search(r'https://my.ukma.edu.ua/course/(\d+)', group['link']).group(1)
                groups[group_id] = group['number']
                subject_model = GroupModel(name, group_id, group['number'], user_id)
                subject_model.save_to_db()
                signuper = GroupSignuper(groups, user.get_cookies())
                if date is None:
                    signuper.execute()
                else:

                    telegram.start(signuper)

        except:
            return {"message": "Some error occurred"}, 500
        return {"message": "Successfully added Groups"}, 201

