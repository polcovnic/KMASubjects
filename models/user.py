import logging

from models.cookie import CookieModel
from db import db
from saz_signuper.loginer import Loginer

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler('logs/models/user.log')
formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class UserModel(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80))
    password = db.Column(db.String(80))
    cookies = db.relationship('CookieModel', lazy='dynamic')

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def save_cookies(self):
        loginer = Loginer()
        cookies = loginer.execute(self.username, self.password)
        for cookie in cookies:
            cookie_model = CookieModel(cookie.get('name'), cookie.get('value'), cookie.get('domain'), self.id)
            try:
                cookie_model.save_to_db()
                logger.info('Successfully saved cookie to db')
            except:
                logger.error('Some error occurred while saving cookie to db')

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def get_cookies(self):
        return [cookie.to_dict() for cookie in self.cookies.all()]

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_by_id(cls, _id):
        return cls.query.filter_by(id=_id).first()
