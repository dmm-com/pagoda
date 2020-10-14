import mock
import re

from airone.lib.test import AironeViewTest
from airone.lib import types as atype
from django.urls import reverse
from django.conf import settings
from entity.models import Entity, EntityAttr
from entry.models import Entry, Attribute, AttributeValue
from user.models import User


class ImportTest(AironeViewTest):
    def test_import_entity(self):
        self.admin_login()

        fp = self.open_fixture_file('entity.yaml')
        resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
        self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks each objects are created safety
        self.assertEqual(Entity.objects.count(), 3)
        self.assertEqual(EntityAttr.objects.count(), 4)

        # checks keeping the correspondence relationship with id and name
        self.assertEqual(Entity.objects.get(id='1').name, 'entity1')
        self.assertEqual(EntityAttr.objects.get(id='5').name, 'attr-obj')

        # checks contains required attributes (for Entity)
        entity = Entity.objects.get(name='entity')
        self.assertEqual(entity.note, 'note1')
        self.assertTrue(entity.status & Entity.STATUS_TOP_LEVEL)

        entity1 = Entity.objects.get(name='entity1')
        self.assertEqual(entity1.note, '')
        self.assertFalse(entity1.status & Entity.STATUS_TOP_LEVEL)

        # checks contains required attributes (for EntityAttr)
        self.assertEqual(entity.attrs.count(), 4)
        self.assertEqual(entity.attrs.get(name='attr-str').type, atype.AttrTypeStr)
        self.assertEqual(entity.attrs.get(name='attr-obj').type, atype.AttrTypeObj)
        self.assertEqual(entity.attrs.get(name='attr-arr-str').type, atype.AttrTypeArrStr)
        self.assertEqual(entity.attrs.get(name='attr-arr-obj').type, atype.AttrTypeArrObj)
        self.assertFalse(entity.attrs.get(name='attr-str').is_mandatory)
        self.assertTrue(entity.attrs.get(name='attr-obj').is_mandatory)

    def test_import_entity_with_unnecessary_param(self):
        self.admin_login()
        warning_messages = []

        fp = self.open_fixture_file('entity_with_unnecessary_param.yaml')
        with mock.patch('dashboard.views.Logger') as lg_mock:
            def side_effect(message):
                warning_messages.append(message)

            lg_mock.warning = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks that warning messagees were outputted
        self.assertEqual(len(warning_messages), 2)
        self.assertTrue(re.match(r'^.*Entity.*Unnecessary key is specified$',
                                 warning_messages[0]))
        self.assertTrue(re.match(r'^.*EntityAttr.*Unnecessary key is specified$',
                                 warning_messages[1]))

        self.assertEqual(Entity.objects.count(), 2)
        self.assertEqual(EntityAttr.objects.count(), 3)

    @mock.patch('import_export.resources.logging')
    def test_import_entity_without_mandatory_param(self, mock_logger):
        self.admin_login()
        warning_messages = []

        fp = self.open_fixture_file('entity_without_mandatory_param.yaml')
        with mock.patch('dashboard.views.Logger') as lg_mock:
            def side_effect(message):
                warning_messages.append(message)

            lg_mock.warning = mock.Mock(side_effect=side_effect)
            mock_logger.exception = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks that warning messagees were outputted
        self.assertEqual(len(warning_messages), 3)
        self.assertTrue(re.match(r"^.*Entity.*Mandatory key doesn't exist$",
                                 str(warning_messages[0])))
        self.assertEqual("The parameter 'type' is mandatory when a new EntityAtter create",
                         str(warning_messages[1]))
        self.assertEqual(str(warning_messages[2]), "refer to invalid entity object")

        self.assertEqual(Entity.objects.count(), 2)

        # checks not to create EntityAttr that refers invalid object
        self.assertEqual(EntityAttr.objects.count(), 2)
        self.assertEqual(EntityAttr.objects.filter(name='attr-arr-obj').count(), 0)

    def test_import_entity_with_spoofing_user(self):
        self.admin_login()
        warning_messages = []

        # A user who creates original mock object
        user = User.objects.create(username='test-user')

        Entity.objects.create(id=3, name='baz-original', created_user=user)

        fp = self.open_fixture_file('entity.yaml')
        with mock.patch('import_export.resources.logging') as lg_mock:
            def side_effect(message):
                warning_messages.append(str(message))

            lg_mock.exception = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks to show warning messages
        msg = r"failed to identify entity object"
        self.assertEqual(len(warning_messages), 4)
        self.assertTrue(all([re.match(msg, x) for x in warning_messages]))

        # checks that import data doens't appied
        entity = Entity.objects.get(id=3)
        self.assertEqual(entity.name, 'baz-original')

        # checks that the EntityAttr objects which refers invalid Entity won't create
        self.assertEqual(entity.attrs.count(), 0)
        self.assertEqual(EntityAttr.objects.filter(name='attr-str').count(), 0)

    def test_import_entry(self):
        self.admin_login()

        fp = self.open_fixture_file('entry.yaml')
        resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
        self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks that imported objects were normally created
        self.assertEqual(Entry.objects.count(), 7)
        self.assertEqual(Attribute.objects.count(), 4)

        # checks that after_save_instance processing was normally worked
        entry = Entry.objects.get(name='srv001')
        self.assertEqual(entry.attrs.count(), 4)
        self.assertEqual(entry.attrs.get(name='attr-str').schema.type, atype.AttrTypeStr)
        self.assertEqual(entry.attrs.get(name='attr-obj').schema.type, atype.AttrTypeObj)
        self.assertEqual(entry.attrs.get(name='attr-arr-str').schema.type, atype.AttrTypeArrStr)
        self.assertEqual(entry.attrs.get(name='attr-arr-obj').schema.type, atype.AttrTypeArrObj)

        # checks that a new AttribueValue was created by import-data
        self.assertEqual(Attribute.objects.get(name='attr-str').values.count(), 2)
        self.assertEqual(Attribute.objects.get(name='attr-obj').values.count(), 1)
        self.assertEqual(Attribute.objects.get(name='attr-arr-str').values.count(), 1)
        self.assertEqual(Attribute.objects.get(name='attr-arr-obj').values.count(), 1)

        # checks that attr has corrected referral
        self.assertEqual(Attribute.objects.get(name='attr-str').schema.referral.count(), 0)
        self.assertEqual(Attribute.objects.get(name='attr-obj').schema.referral.count(), 1)
        self.assertEqual(Attribute.objects.get(name='attr-obj').schema.referral.last().name,
                         'Entity1')
        self.assertEqual(Attribute.objects.get(name='attr-arr-str').schema.referral.count(), 0)
        self.assertEqual(Attribute.objects.get(name='attr-arr-obj').schema.referral.count(), 1)
        self.assertEqual(Attribute.objects.get(name='attr-arr-obj').schema.referral.last().name,
                         'Entity2')

        # checks for the Array String attributes
        attr_value = Attribute.objects.get(name='attr-arr-str').get_latest_value()
        self.assertTrue(attr_value.status & AttributeValue.STATUS_DATA_ARRAY_PARENT)
        self.assertEqual(attr_value.data_array.count(), 2)
        # self.assertTrue(all([x.parent_attrv == attr_value for x in attr_value.data_array.all()]))

        # checks for the Array Object attributes
        attr_value = Attribute.objects.get(name='attr-arr-obj').get_latest_value()
        self.assertTrue(attr_value.status & AttributeValue.STATUS_DATA_ARRAY_PARENT)
        self.assertEqual(attr_value.data_array.count(), 2)
        self.assertTrue(all([x.parent_attrv == attr_value for x in attr_value.data_array.all()]))

        # checks latest flags are correctly set for each AttributeValues
        # - 1 is the latest value of attr 'attr-str'
        # - 1 is the latest value of attr 'attr-obj'
        # - 1 is the latest value of attr 'attr-arr-str', but child attrs don't set latet flag
        # - 1 is the latest value of attr 'attr-arr-obj', but child attrs don't set latet flag
        self.assertEqual(AttributeValue.objects.extra(where=['is_latest > 0']).count(),
                         1 + 1 + 1 + 1)

        # checks that imported Entries were registered to the Elasticsearch
        res = self._es.indices.stats(index=settings.ES_CONFIG['INDEX'])
        self.assertEqual(res['_all']['total']['segments']['count'], Entry.objects.count())

    def test_import_entry_without_mandatory_values(self):
        self.admin_login()
        warns = []

        fp = self.open_fixture_file('entry_without_mandatory_values.yaml')
        with mock.patch('dashboard.views.Logger') as lg_mock:
            def side_effect(message):
                warns.append(message)

            lg_mock.warning = mock.Mock(side_effect=side_effect)
            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
            fp.close()

        # checks for the output wanring messages
        self.assertEqual(len(warns), 2)
        self.assertTrue(any([re.match(r".*The value of .* is needed", x) for x in warns]))
        self.assertTrue(any([re.match(r".*Mandatory key doesn't exist", x) for x in warns]))

        # checks for the imported objects successfully
        self.assertEqual(Entity.objects.count(), 1)
        self.assertEqual(Entry.objects.count(), 1)

    def test_import_entity_with_duplicate_entity(self):
        self.admin_login()
        warning_messages = []

        fp = self.open_fixture_file('entity_with_duplication.yaml')
        with mock.patch('import_export.resources.logging') as lg_mock:
            def side_effect(message):
                warning_messages.append(str(message))

            lg_mock.exception = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks that the duplicate object wouldn't be created
        self.assertEqual(Entity.objects.count(), 3)
        self.assertEqual(EntityAttr.objects.count(), 4)
        self.assertEqual(Entity.objects.get(name='entity').note, 'note1')

        # checks that an exception caused by the duplicate entity is occurred
        self.assertEqual(len(warning_messages), 1)
        self.assertTrue("There is a duplicate entity object (entity)" == warning_messages[0])

    def test_import_entry_with_duplicate_entry(self):
        self.admin_login()
        warning_messages = []

        fp = self.open_fixture_file('entry_with_duplication.yaml')
        with mock.patch('import_export.resources.logging') as lg_mock:
            def side_effect(message):
                warning_messages.append(str(message))

            lg_mock.exception = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        entity = Entity.objects.get(name='Server')

        # checks that the duplicate object wouldn't be created
        self.assertEqual(Entry.objects.count(), 3)
        self.assertEqual(Entry.objects.filter(schema=entity, name='srv001').count(), 1)
        self.assertEqual(Entry.objects.get(schema=entity, name='srv001').id, 14)

        self.assertEqual(len(warning_messages), 1)
        self.assertTrue("There is a duplicate entry object" == warning_messages[0])

    def test_import_entry_referring_invalid_schema(self):
        self.admin_login()
        warning_messages = []

        fp = self.open_fixture_file('entry_with_invalid_schema.yaml')
        with mock.patch('import_export.resources.logging') as lg_mock:
            def side_effect(message):
                warning_messages.append(str(message))

            lg_mock.exception = mock.Mock(side_effect=side_effect)

            resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
            self.assertEqual(resp.status_code, 303)
        fp.close()

        # checks that the duplicate object wouldn't be created
        self.assertEqual(Entry.objects.count(), 2)
        self.assertEqual(len(warning_messages), 1)
        self.assertTrue("Specified entity(invalid_schema) doesn't exist" == warning_messages[0])

    def test_import_entity_with_max_file_size(self):
        self.admin_login()

        fp = self.open_fixture_file('entity_with_max_file_size.yaml')

        # check that the status code is 400
        resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
        self.assertEqual(resp.status_code, 400)
        fp.close()

    def test_import_entry_lack_of_attrvalues(self):
        self.admin_login()

        fp = self.open_fixture_file('entry_lack_of_attrvalues.yaml')
        resp = self.client.post(reverse('dashboard:do_import'), {'file': fp})
        self.assertEqual(resp.status_code, 303)
        fp.close()

        self.assertEqual(Attribute.objects.get(name='attr-str').values.count(), 1)
        self.assertEqual(Attribute.objects.get(name='attr-obj').values.count(), 0)
        self.assertEqual(Attribute.objects.get(name='attr-arr-str').values.count(), 0)
        self.assertEqual(Attribute.objects.get(name='attr-arr-obj').values.count(), 0)

        attr = Attribute.objects.get(name='attr-str')
        attr_value = AttributeValue.objects.last()

        self.assertEqual(attr.get_latest_value(), attr_value)
