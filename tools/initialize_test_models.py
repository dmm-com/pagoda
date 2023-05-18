import os
import sys
from typing import Any, Dict, List, TypedDict
import yaml
import configurations
from django.db.models import Model
from django.db.models.fields.related import ManyToManyField, ForeignKey
from django.db.models.fields import Field


# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()



def create_model_by_prototype(model_name, table_name, prototype):
    import copy

    class Meta:
        pass

    fields = {}
    for field in prototype._meta.fields:
        fields[field.name] = copy.deepcopy(field)

    attrs = {'__module__': "app.models.models", 'Meta': Meta}
    attrs.update(fields)
    model = type(model_name, (models.Model,), attrs)

    return model


def initialize_test_models():
    create_model_by_prototype("AttrTypeString", "table-test01", Model)

if __name__ == "__main__":
    initialize_test_models()
