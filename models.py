from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import(TimedJSONWebSignatureSerializer as Serializer,
                         BadSignature, SignatureExpired)
import random
import string


Base = declarative_base()

# Create secret key to use with Token based authentication
secret_key = ''.join(random.choice(string.ascii_uppercase +
                                   string.digits) for x in xrange(32))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    username = Column(String(32))
    picture = Column(String(250))
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    # Add a method to generate auth tokens here
    def generate_auth_token(self, expiration=600):
        s = Serializer(secret_key, expires_in=expiration)
        return s.dumps({'id': self.id})

    # Add a method to verify auth tokens here
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            # Valid Token, but expired
            return None
        except BadSignature:
            # Invalid Token
            return None
        user_id = data['id']
        return user_id


class Categories(Base):
    __tablename__ = 'categories'

    name = Column(String(250), nullable=False)
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
        }


class CategoryItems(Base):
    __tablename__ = 'category_items'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    categories_id = Column(Integer, ForeignKey('categories.id'))
    categories = relationship(Categories)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
        }


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
