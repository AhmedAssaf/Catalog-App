import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.serializer import loads, dumps
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)

    @property
    def serialize(self):
       return {
           'id': self.id,
           'name': self.name,
           'email' : self.email
       }
    
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    items = relationship("Item", backref="category")

    @property
    def serialize(self):
       return {
           'id': self.id,
           'name': self.name,
           'items' : [i.serialize for i in self.items]
       }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    desc = Column(String(1000))
    category_id = Column(Integer, ForeignKey('category.id'))
    #category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)
    
    @property
    def serialize(self):
       return {
           'id': self.id,
           'name': self.name,
           'desc' : self.desc
       }


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
