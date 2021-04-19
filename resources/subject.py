from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse

from models.subject import SubjectModel
from models.user import UserModel


class Subject(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('subjects', type=dict)

    @jwt_required()
    def post(self):
        data = self.parser.parse_args()['subjects']
        body = data['body']
        date = data['date']
        user_id = get_jwt_identity()
        user: UserModel = UserModel.find_by_id(user_id)
        user.subjects_date = date
        for subject in body:
            subject_model = SubjectModel('default', subject, user_id)
            subject_model.save_to_db()
        return {"message": "Successfully added subjects"}, 201
