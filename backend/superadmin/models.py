from mongoengine import Document, StringField, IntField, EmailField, BooleanField, DateTimeField
from django.contrib.auth.hashers import make_password, is_password_usable
from datetime import datetime, timedelta

# Create your models here.
class User(Document) :
    meta = {'collection': 'User_Col'}

    first_name = StringField(required=True)
    last_name = StringField(required=True)
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    phone = StringField(required=True)
    password = StringField(required=True)
    user_type = IntField(default=3) # 1 = superadmin & 2 = admin & 3 = user
    is_verified = BooleanField(default=False)
    is_active = BooleanField(default=False)
    last_login = DateTimeField()
    date_joined = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        if self.password and not is_password_usable(self.password):
            self.password = make_password(self.password)
        super(User, self).save(*args, **kwargs)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    @property
    def is_authenticated(self):
        return self.is_active
    
class OTP(Document):
    meta = {
        'collection': 'OTP_Col',
        'indexes': [
            {
                'fields': ['expired_at'],
                'expireAfterSeconds': 0
            }
        ]
    }

    username = StringField(required=True)
    code = IntField(required=True)
    created_at = DateTimeField(default=datetime.utcnow)
    expired_at = DateTimeField(default=lambda: datetime.utcnow() + timedelta(minutes=3))