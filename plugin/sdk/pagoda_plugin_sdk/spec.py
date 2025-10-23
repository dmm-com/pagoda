# This describes Model's specification that a Plugin requires (a.k.a. AdaptedEntity before)
class ModelSpec(object):
    def __init__(self, name=None, attrs={}, inheritance=None, exclude_attrs=[]):
        self.name = name
        self.attrs = attrs
        self.inheritance = inheritance
        self.exclude_attrs = exclude_attrs

    def get_attrs(self):
        returned_attrs = self.attrs
        if self.inheritance:
            inheritances = []
            if isinstance(self.inheritance, str):
                inheritances = [self.inheritance]
            elif isinstance(self.inheritance, list):
                inheritances = self.inheritance

            for ae_name_key in inheritances:
                inherited_adapted_entity = ModelSpec.get(ae_name_key)

                # This merges with inherited ModelSpec's attrs
                returned_attrs = dict(returned_attrs, **inherited_adapted_entity.get_attrs())

        # This excludes attrs which are explicitly set to exclude
        return {k: v for k, v in returned_attrs.items() if k not in self.exclude_attrs}

    def is_inherited(self, ae_name) -> bool:
        if isinstance(self.inheritance, str):
            return ae_name == self.inheritance
        elif isinstance(self.inheritance, list):
            return ae_name in self.inheritance

        return False

    def get_attr(self, name):
        return self.get_attrs()[name]

    def get_attrname(self, name):
        return self.get_attrs()[name]["name"]


# NOTE: we have to consider to re-design about following structure that refers
#       MODEL_SPEC object fomr this class.
#
#    @classmethod
#    def get(kls, entity_key):
#        return MODEL_SPEC[entity_key]
#
#    @classmethod
#    def get_by_entity_name(kls, entity_name):
#        for adapted_entity in kls.get_actual_entities():
#            if adapted_entity.name == entity_name:
#                return adapted_entity
#
#    @classmethod
#    def get_actual_entities(kls):
#        return [x for x in MODEL_SPEC.values() if x.name is not None]
#
#    @classmethod
#    def get_inherited_entities(kls, inheritance_name: str) -> List[str]:
#        return [x.name for x in kls.get_actual_entities() if x.is_inherited(inheritance_name)]
