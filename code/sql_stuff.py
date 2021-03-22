#!/usr/bin/python3
# DB Management
from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy import Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

import streamlit as st
import hashing as hash

def get_connection():
    engine = create_engine(
        'sqlite:///data.db', connect_args={'check_same_thread': False} )
    return engine

engine = get_connection()
Session = sessionmaker(bind=engine)
session = Session()


Base = declarative_base()
# Model
class User(Base):
    __tablename__ = 'userstable'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(300))
    role_id = Column(Integer, ForeignKey('role.id'))

    def __repr__(self):
        return "<User(username='%s', password='%s', role='%s')>" % (self.username, self.password, self.role)
class Role(Base):
    __tablename__ = 'role'
    id = Column(Integer, Sequence('role_id_seq'), primary_key=True)
    role = Column(String(50), nullable=False, unique=True)
    users = relationship("User", backref="role")


    def __repr__(self):
        return "<Role(role='%s')>" % (self.role)

class Headings(Base):
    __tablename__ = 'headingstable'
    id = Column(Integer, Sequence('head_id_seq'), primary_key=True)
    header = Column(String(200), nullable=False, unique=True)
    alias = Column(String(200))
    description = Column(String(1000))
    keywd = Column(String(20))

    def __repr__(self):
        return "<Headings(header='%s', alias='%s', description='%s', keywd='%s')>" % (self.header, \
            self.alias, self.description, self.keywd)

class Metrics(Base):
    __tablename__ = 'metric'
    id = Column(Integer, Sequence('metric_id_seq'), primary_key=True)
    metric = Column(String(100), nullable=False, unique=True)
    description = Column(String(1000))

    def __repr__(self):
        return "<Metric(metric='%s', description='%s')>" % (self.metric, self.description)

# DB actions
def create_tables():
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    for table in ['userstable', 'headingstable', 'role', 'metric', 'sarheadtable']:
        if table not in table_names:
            Base.metadata.create_all(engine)
            break

def view_all_users(kind='show'):
    user_list = []
    for instance in session.query(User).order_by(User.username):
        if kind == 'show':
            user_list.append([instance.username, instance.role.role])
        else:
            user_list.append([instance.username][0])
    return user_list

def login_user(username, password):
    query = session.query(User.password).filter(User.username == username)
    if query.first():
        hpassword = query.first()[0]
        result = hash.verify_password(hpassword, password)
        return result
    else:
        return False

def add_userdata(username, password, role='user'):
    query = session.query(User.username).filter(User.username == username)
    role_id = session.query(Role.id).filter(Role.role == role)
    if query.first():
       return False 
    hpassword = hash.hash_password(password)
    new_user = User(username=username, password=hpassword, role_id=role_id)
    session.add(new_user)
    session.commit()
    return True

def change_password(username, password):    
    user = session.query(User).filter(User.username == username)
    if user.first():
        hpassword = hash.hash_password(password)
        user.first().password = hpassword
        session.commit()

def modify_user(username, role):
    user = session.query(User).filter(User.username == username)
    role_id = session.query(Role.id).filter(Role.role == role)
    if user.first():
        user.first().role_id = role_id
        session.commit()

def delete_user(username):
    session.query(User).filter(User.username == username).delete()
    x = session.commit()
    return x

def get_role(username):
    user = session.query(User).filter(User.username == username)
    if user.first():
        return user.first().role.role

def add_metric(metric, description):
    query = session.query(Metrics.metric).filter(Metrics.metric == metric)
    if not query.first():
        new_metric = Metrics(metric=metric, description=description)
        session.add(new_metric)
        session.commit()

def ret_metric_description(metric):
    metric = session.query(Metrics).filter(Metrics.metric == metric)
    if metric.first():
        return(metric.first().description)
    else:
        return('','')

def view_all_metrics():
    m_list = []
    for instance in session.query(Metrics).order_by(Metrics.metric):
        m_list.append([instance.metric, instance.description])
    return m_list

def delete_metric(metric):
    session.query(Metrics).filter(Metrics.metric == metric).delete()
    x = session.commit()
    return x

def ret_all_headers(kind='return'):
    h_list = []
    for instance in session.query(Headings).order_by(Headings.header):
        if kind == 'return':
            h_list.append([instance.header][0])
        elif kind == 'show':
            h_list.append([instance.header, instance.description, instance.alias, instance.keywd])

    return h_list


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}

def get_header_prop(header, property):
    if property == 'alias':
        org_header = header
        header = header[0:1]
        unlist_header = " ".join(repr(e) for e in header).replace("'","")
        query = session.query(Headings).filter(Headings.header.ilike(f'{unlist_header}%'))
        if query.first():
            # multiple header with same metric, e.g. %usr
            if len(query.all()) > 1:
                # helper vars if header has no related alias
                col_field = []
                for col in query:
                    counter = 0
                    result_dict = object_as_dict(col)
                    header_len = len(result_dict['header'].split())
                    for item in result_dict['header'].split():
                        if item not in org_header:
                            # count how much different items compared to header
                            counter += 1
                    if counter == 0:
                        return result_dict['alias']
                    # save alias for each len of header field
                    else:
                        col_field.append([result_dict['alias'], counter])

                # try to find the nearest alias
                # header differs by one metric
                l_counter = 1
                index = 0
                for entry in col_field:
                    counter = entry[1]
                    if counter <= l_counter:
                        l_counter = counter
                        index = col_field.index(entry)
                if len(org_header) - header_len <= abs(2):
                        return col_field[index][0]

            # header differs by more than one metric
            else:
                return query.first().alias
    else:
        query = session.query(Headings).filter(Headings.header.ilike(f'{header}%'))
        if query.first():
            if property == 'description':
                return query.first().description
            elif property == 'keywd':
                return query.first().keywd

def get_header_from_alias(alias):
    header = session.query(Headings).filter(Headings.alias == alias)
    if header.first():
        return header.first().header
    else:
        return None

def add_header(header, description, alias, keywd=None):
    query = session.query(Headings.header).filter(Headings.header == header)
    if not query.first():
        # normalize header whitespaces
        header = " ".join(header.split())
        new_header = Headings(header=header, description=description, alias=alias, keywd=keywd)
        session.add(new_header)
        session.commit()

def delete_header(header):
    session.query(Headings).filter(Headings.header == header).delete()
    x = session.commit()
    return x

def update_header(o_header, header=None, alias=None, description=None, keyword=None):
    query = session.query(Headings).filter(Headings.header == o_header)
    new_header = Headings(header=header, description=description, alias=alias, keywd=keyword)
    if query.first():
        query.delete()
        session.add(new_header)
        session.commit()

def add_role(role):
    query = session.query(Role.role).filter(Role.role == role)
    if not query.first():
        new_role = Role(role=role)
        session.add(new_role)
        session.commit()

def ret_all_roles():
    r_list = []
    for instance in session.query(Role).order_by(Role.role):
        r_list.append([instance.role][0])
    return r_list

def delete_role(role):
    session.query(Role).filter(Role.role == role).delete()
    x = session.commit()
    return x

if __name__ == '__main__':
    create_tables()
    add_role('user')        
    add_role('admin')        
    modify_user('jschaef', 'admin')
    get_role('jschaef')
    print(ret_metric_description('load'))
    print(ret_metric_description('test'))
