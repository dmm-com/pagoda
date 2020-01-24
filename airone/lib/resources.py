import importlib
import tablib

from import_export.resources import ModelResource
from acl.models import ACLBase
from airone.lib.acl import ACLType


class AironeModelResource(ModelResource):
    COMPARING_KEYS = []
    DISALLOW_UPDATE_KEYS = []

    def __init__(self, *args, **kwargs):
        super(AironeModelResource, self).__init__(*args, **kwargs)

        # This parameter is needed to check that imported object has permission
        # to add/update it by the user who import data.
        self.request_user = None

    """
    This private method checks that two instance has same content in each attribute.
    """
    def _is_updated(self, comp1, comp2):
        return any([getattr(comp1, x) != getattr(comp2, x) for x in self.COMPARING_KEYS])

    def validate_update(self, new, old):
        # This cancels update when the value of disallow update key is updated.
        if not all([getattr(new, x) == getattr(old, x) for x in self.DISALLOW_UPDATE_KEYS]):
            return False
        return True

    def skip_row(self, instance, original):
        # the case of creating new instance
        if not self._meta.model.objects.filter(id=instance.id).exists():
            # Inhibits the spoofing
            if isinstance(instance, ACLBase) and instance.created_user != self.request_user:
                return True

        # the case of instance is updated
        elif self._is_updated(instance, original):
            # the case user try to update but he doen't have writable permition
            if not self.request_user.has_permission(instance, ACLType.Writable):
                return True

            # the case user try to change params which are disallow to update
            if not self.validate_update(instance, original):
                return True

        return False

    # event handler at calling after completion of import processing
    @classmethod
    def after_import_completion(self, results):
        pass

    @classmethod
    def import_data_from_request(self, data, request_user):
        resource = getattr(importlib.import_module(self._IMPORT_INFO['resource_module']),
                           self._IMPORT_INFO['resource_model_name'])()
        if not resource:
            raise RuntimeError("Resource object is not defined")

        # set user who import the data for checking permission
        resource.request_user = request_user

        # check mandatory keys are existed, or not
        if not all([x in data for x in self._IMPORT_INFO['mandatory_keys']]):
            raise RuntimeError("Mandatory key doesn't exist")

        # check that mandatory values is set
        if ('mandatory_values' in self._IMPORT_INFO and
                any(not data[x] for x in self._IMPORT_INFO['mandatory_values'])):
            raise RuntimeError("The value of '%s' is needed" %
                               str(self._IMPORT_INFO['mandatory_values']))

        # check unnecessary parameters are specified, or not
        if not all([x in self._IMPORT_INFO['header'] for x in data.keys()]):
            raise RuntimeError("Unnecessary key is specified")

        # get dataset to import
        dataset = tablib.Dataset([x in data and data[x] or '' for x in self._IMPORT_INFO['header']],
                                 headers=self._IMPORT_INFO['header'])

        return resource.import_data(dataset)
