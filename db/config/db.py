from pymongo import MongoClient
import os
conn = MongoClient('mongodb://localhost:27017/?replicaSet=rs')


db = conn.hive

# def coll(collection):
#     return {
#         'users': db.users
#     }[collection]


# def read_one(collection_name, id):
#     coll(collection_name).find_one
