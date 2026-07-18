from django.apps import AppConfig


class DjangoOrmConfig(AppConfig):
    name = "adapters.persistence.django_orm"
    label = "django_orm"  # AUTH_USER_MODEL = "django_orm.User" depends on this label
    default_auto_field = "django.db.models.BigAutoField"
