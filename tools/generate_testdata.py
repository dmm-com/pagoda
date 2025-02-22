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

# Constants for reference hierarchy
REFERENCE_DEPTH = 3
ENTRIES_PER_LEVEL = 2


class ReferenceLevel:
    def __init__(self, entity: Entity, entries: list[Entry]):
        self.entity = entity
        self.entries = entries


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


def generate_reference_hierarchy(user: User, suffix: str) -> list[ReferenceLevel]:
    levels: list[ReferenceLevel] = []

    # First, create entities and entries for all levels
    for level in range(1, REFERENCE_DEPTH + 1):
        entity = Entity.objects.create(
            name=f"Referred_Entity_L{level}_{suffix}",
            is_active=True,
            created_user=user,
        )

        # Add string attribute to the entity
        string_attr = EntityAttr.objects.create(
            parent_entity=entity,
            name="Attr_string",
            type=AttrType.STRING,
            is_active=True,
            created_user=user,
        )

        entries = [
            Entry.objects.create(
                schema=entity,
                name=f"Referred_Entry_L{level}_{suffix}_{i}",
                is_active=True,
                created_user=user,
            )
            for i in range(ENTRIES_PER_LEVEL)
        ]

        # Set string attribute value for each entry
        for entry in entries:
            string_entry_attr = entry.add_attribute_from_base(string_attr, user)
            string_entry_attr.add_value(user, f"string_value_{_random_string()}")

        levels.append(ReferenceLevel(entity, entries))

    # Set up reference relationships from upper to lower levels (L1->L2->L3->...)
    # The lowest level has no reference
    for level in range(REFERENCE_DEPTH - 1):
        current_level = levels[level]
        next_level = levels[level + 1]

        # Add reference attribute to the current level's entity
        attr = EntityAttr.objects.create(
            parent_entity=current_level.entity,
            name=f"ref_L{level + 2}",
            type=AttrType.OBJECT,
            is_active=True,
            created_user=user,
        )
        attr.referral.add(next_level.entity)

        # Set random reference to next level's entry for each current level entry
        for entry in current_level.entries:
            entry_attr = entry.add_attribute_from_base(attr, user)
            entry_attr.add_value(user, random.choice(next_level.entries))

    return levels


def generate_testdata(num_entities: int, num_entries: int, suffix: str):
    user = User.objects.first()
    if not user:
        user = User.objects.create(username="testuser", email="testuser@example.com")
        user.set_password("password")
        user.save()

    # Generate reference hierarchy instead of single reference entity
    reference_levels = generate_reference_hierarchy(user, suffix)

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
                # Reference L1 entity for root entities
                entity_attr.referral.add(reference_levels[0].entity)

    ref_groups = [
        Group.objects.create(name=f"Referred_Group_{suffix}_{i}", is_active=True) for i in range(2)
    ]
    ref_roles = [
        Role.objects.create(name=f"Referred_Role_{suffix}_{i}", is_active=True) for i in range(2)
    ]

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
                        reference_levels[0].entries,  # Use L1 entries as referrals
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
