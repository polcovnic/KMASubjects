from db import db


class GroupModel(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    link = db.Column(db.String)
    number = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('UserModel')

    def __init__(self, name, link, number, user_id):
        self.name = name
        self.link = link
        self.number = number
        self.user_id = user_id

    def json(self):
        return {
            "link": self.link,
            "number": self.number,
            "name": self.name
        }

    @classmethod
    def find_by_name(cls, name):
        return cls.query.filter_by(name=name).first()

    @classmethod
    def find_by_user_id(cls, user_id):
        return cls.query.filter_by(user_id=user_id).first()

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()
