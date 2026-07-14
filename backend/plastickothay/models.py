# from django.db import models
from mongoengine import Document, StringField, IntField, EmailField, FloatField, DateTimeField, ReferenceField
from datetime import datetime
from superadmin.models import User

# Create your models here.
class Post(Document) :
    meta = {'collection': 'Post_Col'}
    user = ReferenceField(User, required=False, null=True)
    name = StringField(required=True)
    email = EmailField(required=True)
    pN = StringField(required=True)
    severity = IntField(required=True) # 1-5
    imageID = StringField(required=True)
    lat = FloatField(required=True)
    lon = FloatField(required=True)
    description = StringField(default="No description provided.")
    status = IntField(default=2) # 0 = rejected, 1 = accepted, 2 = pending
    created = DateTimeField(default=datetime.utcnow)

class Rate(Document) :
    meta = {'collection': 'Rate_Col'}