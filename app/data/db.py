import firebase_admin
from firebase_admin import db, storage, credentials
import json
import os


class Data:
    __instance = None

    def __init__(self) -> None:
        if not Data.__instance:
            fb_admin_struct = json.loads(os.environ['FIREBASE_AUTH'], strict=False)
            cred = credentials.Certificate(fb_admin_struct)
            firebase_admin.initialize_app(cred, {
                'databaseURL': os.environ['FIREBASE_URL'],
                'storageBucket': os.environ["FIREBASE_STORAGE_URL"]
            })
            Data.__instance = (db, storage)
        else:
            raise Exception("This is a singleton!")

    @classmethod
    def get_db_instance(cls):
        if Data.__instance is None:
            Data()
        return Data.__instance[0]

    @classmethod
    def get_storage_instance(cls):
        if Data.__instance is None:
            Data()
        return Data.__instance[1]
