import random
import base64
from uuid import uuid4


def generate_short_id(size=9, chars='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    return ''.join(random.choice(chars) for _ in range(size))

def get_new_room_uidb64(short_id: str):
    short_id_with_time = str(uuid4().hex)[:8]+'-'+ short_id +'-'+ str(uuid4().hex)[:8]
    sample_string_bytes = short_id_with_time.encode("ascii")
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")
    return base64_string

def decode_room_uidb64(value: str):
    base64_bytes = value.encode("ascii")
    sample_string_bytes = base64.b64decode(base64_bytes)
    sample_string = sample_string_bytes.decode("ascii")
    short_id = sample_string.split('-')[1]
    return short_id