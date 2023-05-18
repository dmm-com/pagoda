import os
import sys
from optparse import OptionParser

import configurations

# append airone directory to the default path

sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

from django.db import connections, models
from user_models.models import UserModel


def alter_model(model_name, fields={}):
    # This is necessary to handle field that refers LB model
    UserModel.declare("LB", {"name": models.CharField(max_length=200, unique=True)})
    UserModel.declare("LBServiceGroup")

    model = UserModel.declare(model_name, fields)

    # DB migration
    connection = connections["default"]
    with connection.schema_editor(collect_sql=False, atomic=True) as se:
        #print(model._meta.get_field("lb"))
        se.add_field(model, model._meta.get_field("lb_service_group"))


if __name__ == "__main__":
    alter_model(
        "LBVirtualServer",
        {
            "name": models.CharField(max_length=200, unique=True),
            "lb": models.ForeignKey("LB", null=True, on_delete=models.SET_NULL, verbose_name="LB"),
            "lb_service_group": models.ManyToManyField(
                "LBServiceGroup", verbose_name="LBServiceGroup"
            ),
        },
    )

