def serialize_dict(a) -> dict:
    return {**{'id':str(a[i]) for i in a if i == '_id'}, **{i:a[i] for i in a if i != '_id' and i != 'hashed_password'}}

def serialize_list(a) -> list:
    return [serialize_dict(i) for i in a ]

def auth_serializer(a) -> dict:
    return {**{'id':str(a[i]) for i in a if i == '_id'}, **{i:a[i] for i in a if i != '_id' }}

