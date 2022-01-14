from db.config.db import db



def find_one(dbcollection, object):
    instance = dbcollection.find_one(object)
    return instance

def find_one_and_update(dbcollection, object, **kwargs):
    dbcollection.find_one_and_update(object, kwargs)

def insert_one(dbcollection, object):
    dbcollection.insert_one(object)

def find_one_and_delete(dbcollection, object):
    return dbcollection.find_one_and_delete(object)

def find(dbcollection):
    return dbcollection.find()