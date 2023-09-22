from db import Data


class SDBObj:
    def __init__(self, ref_url):
        self.ref_url = ref_url
        self.db = Data.get_db_instance()
        self.ref = self.db.reference(self.ref_url)
        self.data = None

        self.initialized = False

        self.load()

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, val):
        self.data[key] = val

    def __contains__(self, key):
        return key in self.data

    def get(self, key, default=None):
        if key in self.data:
            return self.data[key]
        return default

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()

    def load(self):
        self.data = self.ref.get()
        if self.data is not None:
            self.initialized = True
        return True

    def save(self):
        self.ref.set(self.data)
        return True


class User(SDBObj):

    def __init__(self, user_id):
        super().__init__(f'/users/{user_id}')

        self.user_id = user_id

    def initialize(self):
        self.data = {
            "user_id": self.user_id
        }
