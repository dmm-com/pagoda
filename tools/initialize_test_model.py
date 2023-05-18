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


def generate(model_name, fields={}):
    """
    NOTE: Dynamic generate model class for testing
    """

    # creating class dynamically
    model = type(
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

    # DB migration
    connection = connections["default"]
    with connection.schema_editor(collect_sql=False, atomic=True) as se:
        # se.delete_model(model)
        se.create_model(model)


if __name__ == "__main__":
    # generate("AttrTypeString", {"value": models.CharField(max_length=200, unique=True)})
    generate("LB", {"name": models.CharField(max_length=200, unique=True)})
    generate("LBServiceGroup", {"name": models.CharField(max_length=200, unique=True)})
    generate(
        "LBVirtualServer",
        {
            "name": models.CharField(max_length=200, unique=True),
            "lb": models.ForeignKey("LB", null=True, on_delete=models.SET_NULL, verbose_name="LB"),
            "lb_service_group": models.ManyToManyField(
                "LBServiceGroup", verbose_name="LBServiceGroup"
            ),
        },
    )
