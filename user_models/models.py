from django.db import models
from entity.models import Entity, EntityAttr

# Create your models here.

class UserModel(object):
    @classmethod
    def list(klass):
        # This returns user specified Models from Entity definition
        return [{
            "model_name": e.model_name,
            "label": e.name,
            "attrs": [{
                "model_name": a.model_name,
                "label": a.name,
                "type": a.type,
                "referral": a.referral.first(),  ## note it must be changed
            } for a in e.attrs.filter(is_active=True)]
        } for e in Entity.objects.filter(is_active=True)]

    @classmethod
    def get(klass, model_name):
        entity = Entity.objects.filter(name=model_name, is_active=True).first()
        if not entity:
            return

        return {
            "model_name": entity.model_name,
            "label": entity.name,
            "attrs": [{
                "model_name": entity.model_name,
                "label": a.name,
                "type": a.type,
                "referral": a.referral.first(),  ## note it must be changed
            } for a in entity.attrs.filter(is_active=True)]
        }

    @classmethod
    def load(klass, model_name):
        # load Model from Entity/EntityAttr
        pass

    @classmethod
    def declare(klass, model_name, fields={}):
        # declare Model class
        return type(
            model_name,
            (models.Model,),
            dict(
                {
                    # data members (Django)
                    # "name": models.CharField(max_length=200, unique=True),
                    # Django integration
                    "__module__": "user_models",
                },
                **fields
            ),
        )
