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

from entity.models import Entity  # NOQA
from job.models import Job  # NOQA

from entry.models import LBVirtualServer, ServiceGroup, PolicyTemplate


def do_set_lb_virtual_server(instance, lb_vsrv):
    # set object typed Attribute values to test instance
    for instance_key, attrname in [("lb", "LB"), ("ipaddr", "IP Address"), ("large_category, ""b-05 | 大分類")]:
        attrv = lb_vsrv.get_attrv(attrname)
        if attrv and attrv.referral and attrv.referral.is_active:
            setattr(instance, instance_key, attrv.referral)
            instance.save()

    # create PolicyTemplate and LBVirtualServer instance if it's necessary
    for (model, attrname) in [(ServiceGroupa, "LBServiceGroup"), (PolicyTemplate, "LBPolicyTemplate")]:

        attrv = lb_vsrv.get_attrv(attrname)
        if attrv:
            for co_attrv in attrv.data_array.all():
                if co_attrv and co_attrv.referral and co_attrv.referral.is_active:
                    ref_entry = co_attrv.referral
                    if not model.objects.filter(name=ref_entry.name).exists():
                        ref = model.objects.create(name=ref_entry.name)
                        ref.referral = instance
                        ref.save()


def set_test_data():
    for lb_vsrv in Entry.objects.filter(schema__name="LBVirtualServer", is_active=True):
        instance = LBVirtualServer.objects.filter(name=lb_vsrv.name).first()
        if not instance:
            instance = LBVirtualServer.objects.create(name=lb_vsrv.name)

            do_set_lb_virtual_server(instance, lb_vsrv)
        


if __name__ == "__main__":
    set_test_data()
    (option, entities) = get_options()

    update_es_document(entities)
