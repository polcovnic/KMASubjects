from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_restful import Resource, reqparse
from flask_cors import cross_origin
from bs4 import BeautifulSoup
import requests

from models.subject import SubjectModel
from models.user import UserModel
from saz_signuper.sender import Sender
from saz_signuper.subject_signuper import SubjectSignuper


class Subject(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('subjects', type=dict)

    @jwt_required()
    @cross_origin()
    def post(self):
        data = self.parser.parse_args()['subjects']
        body = data['body']
        date = data['date']
        name = data['name']
        user_id = get_jwt_identity()
        user: UserModel = UserModel.find_by_id(user_id)
        user.subjects_date = date
        for subject in body:
            subject_model = SubjectModel(name, subject, user_id)
            subject_model.save_to_db()
        if date is None:
            signuper = SubjectSignuper(body, user.get_cookies())
            signuper.execute()
        return {"message": "Successfully added subjects"}, 201


class SubjectName(Resource):
    parser = reqparse.RequestParser()
    parser.add_argument('link', type=str)
    sender = Sender()

    @cross_origin()
    def get(self):
        link = self.parser.parse_args('link')
        return self.get_name(link)

    @classmethod
    def get_name(cls, link) -> str:
        response = cls.sender.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        soup.h1.small.decompose()
        return soup.h1.text.strip('\n\t')
