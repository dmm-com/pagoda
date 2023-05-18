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


def generate():
    """
    NOTE: Dynamic generate model class for testing
    """

    # constructor
    def constructor(self, arg):
        self.constructor_arg = arg

    # method
    def displayMethod(self, arg):
        print(arg)

    # class method
    @classmethod
    def classMethod(cls, arg):
        print(arg)

    # dummy TODO describe something in settings.py ???
    module = "entry"

    # creating class dynamically
    Geeks = type("Geeks", (models.Model,), {
        # constructor
        "__init__": constructor,

        # data members (Django)
        "name": models.CharField(max_length=200, unique=True),
        # data members
        "string_attribute": "Geeks 4 geeks !",
        "int_attribute": 1706256,

        # member functions
        "func_arg": displayMethod,
        "class_func": classMethod,

        # Django integration
        "__module__": module,
    })

    # debug print
    obj = Geeks("constructor argument")
    print(obj.constructor_arg)
    print(obj.string_attribute)
    print(obj.int_attribute)
    obj.func_arg("Geeks for Geeks")
    Geeks.class_func("Class Dynamically Created !")

    # DB migration
    connection = connections["default"]
    with connection.schema_editor(collect_sql=False, atomic=True) as se:
        se.delete_model(Geeks)
        se.create_model(Geeks)


if __name__ == "__main__":
    generate()
