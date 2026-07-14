from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from superadmin.models import User
from bson import ObjectId
from datetime import datetime

class MongoBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = User.objects(__raw__={"$or": [{"username": username}, {"email": username}]}).first()
            if user and check_password(password, user.password):
                user.last_login = datetime.now()
                user.is_active = True
                user.save()
                return user
        except User.DoesNotExist:
            return None
        except Exception as e:
            return None

    def get_user(self, user_id):
        try:            
            return User.objects.get(pk=ObjectId(user_id))
        except User.DoesNotExist:
            return None
        except Exception as e:
            return None
