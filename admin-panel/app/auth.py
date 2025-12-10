from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, name=None, role=None):
        self.id = id
        self.name = name
        self.role = role
    
    # УДАЛИТЬ ВСЕ ЭТИ СТРОКИ:
    # self.is_authenticated = True
    # self.is_active = True
    # self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)