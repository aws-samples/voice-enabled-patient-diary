
import json


def read_file(file_path):
    with open(file_path, 'r') as f:
        file = f.read()
    return file


def load_json_file(file_path):
    return json.loads(read_file(file_path))
