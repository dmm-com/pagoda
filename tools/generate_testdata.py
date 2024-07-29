"""
Test data generator, generates most of major model (roughly random) data in Pagoda, easily, fast.
NOTE it doesn't make indexes for ES. Make it yourself if you need.

How to use:
$ python tools/generate_testdata.py [num_entities] [num_entries]
- num_entities: The number of entities to generate.
- num_entries: The number of entries to generate for each entity.
"""

import os
import random
import string
import sys
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import date, datetime, timezone
from optparse import OptionParser

import configurations

from airone.lib.types import AttrType, AttrTypeValue
from entity.models import Entity, EntityAttr
from entry.models import Attribute, Entry
from group.models import Group
from role.models import Role
from user.models import User

# append airone directory to the default path
sys.path.append("./")

# prepare to load the data models of AirOne
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "airone.settings")
os.environ.setdefault("DJANGO_CONFIGURATION", "Dev")

# load AirOne application
configurations.setup()

# the target attr types don't contain meta types
TARGET_ATTR_TYPES = {
    name: type
    for name, type in AttrTypeValue.items()
    if type not in [AttrType._NAMED, AttrType._ARRAY]
}


def _random_string(length=10) -> str:
    letters = string.ascii_letters
    return "".join(random.choice(letters) for i in range(length))


def _get_attribute_value(
    type: AttrType, referrals: list[Entry], groups: list[Group], roles: list[Role]
) -> (
    str
    | list[str]
    | bool
    | dict
    | list[dict]
    | Entry
    | Group
    | Role
    | list[Entry]
    | list[Group]
    | list[Role]
    | date
    | datetime
):
    extra = _random_string(10)

    match type:
        case AttrType.STRING:
            return f"string_value_{extra}"
        case AttrType.ARRAY_STRING:
            return [f"array_string_value_{extra}_{i}" for i in range(2)]
        case AttrType.OBJECT:
            return random.choice(referrals)
        case AttrType.ARRAY_OBJECT:
            return random.sample(referrals, k=random.randint(1, len(referrals)))
        case AttrType.NAMED_OBJECT:
            return {"name": f"named_object_value_{extra}", "id": random.choice(referrals)}
        case AttrType.ARRAY_NAMED_OBJECT:
            return [
                {"name": f"array_named_object_value_{extra}_{i}", "id": r}
                for i, r in enumerate(random.sample(referrals, k=random.randint(1, len(referrals))))
            ]
        case AttrType.GROUP:
            return random.choice(groups)
        case AttrType.ARRAY_GROUP:
            return random.sample(groups, k=random.randint(1, len(groups)))
        case AttrType.BOOLEAN:
            return random.choice([True, False])
        case AttrType.TEXT:
            return f"text_value_{extra}"
        case AttrType.DATE:
            return datetime.now(tz=timezone.utc).date()
        case AttrType.ROLE:
            return random.choice(roles)
        case AttrType.ARRAY_ROLE:
            return random.sample(roles, k=random.randint(1, len(roles)))
        case AttrType.DATETIME:
            return datetime.now(tz=timezone.utc)
        case _:
            raise ValueError(f"Invalid data type: {type}")


def _generate_entry(
    entity: Entity,
    user: User,
    suffix: str,
    ref_entries: list[Entry],
    ref_groups: list[Group],
    ref_roles: list[Role],
) -> None:
    entry = Entry.objects.create(
        schema=entity, name=f"Entry_{suffix}", is_active=True, created_user=user
    )

    attrs: list[Attribute] = []
    for entity_attr in entity.attrs.all():
        attrs.append(entry.add_attribute_from_base(entity_attr, user))

    for attr in attrs:
        attr.add_value(
            user,
            _get_attribute_value(AttrType(attr.schema.type), ref_entries, ref_groups, ref_roles),
        )


def generate_testdata(num_entities: int, num_entries: int, suffix: str):
    user = User.objects.first()
    if not user:
        user = User.objects.create(username="testuser", email="testuser@example.com")
        user.set_password("password")
        user.save()

    ref_entity = Entity.objects.create(
        name=f"Referred_Entity_{suffix}", is_active=True, created_user=user
    )
    ref_entries = [
        Entry.objects.create(
            schema=ref_entity,
            name=f"Referred_Entry_{suffix}_{i}",
            is_active=True,
            created_user=user,
        )
        for i in range(2)
    ]
    ref_groups = [
        Group.objects.create(name=f"Referred_Group_{suffix}_{i}", is_active=True) for i in range(2)
    ]
    ref_roles = [
        Role.objects.create(name=f"Referred_Role_{suffix}_{i}", is_active=True) for i in range(2)
    ]

    entities: list[Entity] = []
    for i in range(num_entities):
        entities.append(
            Entity.objects.create(name=f"Entity_{i}_{suffix}", is_active=True, created_user=user)
        )

    for i, entity in enumerate(entities):
        for name, type in TARGET_ATTR_TYPES.items():
            entity_attr = EntityAttr.objects.create(
                parent_entity=entity,
                name=f"Attr_{name}_{i}_{suffix}",
                type=type,
                is_active=True,
                created_user=user,
            )
            if type in [
                AttrType.OBJECT,
                AttrType.ARRAY_OBJECT,
                AttrType.NAMED_OBJECT,
                AttrType.ARRAY_NAMED_OBJECT,
            ]:
                entity_attr.referral.add(ref_entity)
            entity.attrs.add(entity_attr)

    with ThreadPoolExecutor() as executor:
        futures: list[Future] = []
        for i, entity in enumerate(entities):
            for j in range(num_entries):
                futures.append(
                    executor.submit(
                        _generate_entry,
                        entity,
                        user,
                        f"{i}_{j}_{suffix}",
                        ref_entries,
                        ref_groups,
                        ref_roles,
                    )
                )
        for i, future in enumerate(futures):
            future.result()
            print(f"Progress: entry creation {i}/{len(futures)}")


def get_options():
    parser = OptionParser(usage="%prog [options] [num_entities] [num_entries]")
    return parser.parse_args()


if __name__ == "__main__":
    (options, args) = get_options()
    if len(args) != 2:
        print("Usage: %prog [options] [num_entities] [num_entries]")
        sys.exit(1)

    num_entities = int(args[0])
    num_entries = int(args[1])

    ts = datetime.now().strftime("%Y%m%d%H%M%S")

    generate_testdata(num_entities, num_entries, ts)

    print(f"Finished; generated test data timestamp: {ts}")
