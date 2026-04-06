from typing import TYPE_CHECKING, Any

from django.db import models

from airone.lib.types import AttrType

if TYPE_CHECKING:
    from django.db.models import Manager, QuerySet

    from entry.models import Entry


class IsolationParent(models.Model):
    entity = models.ForeignKey(
        "entity.Entity", on_delete=models.CASCADE, related_name="isolation_rules"
    )

    if TYPE_CHECKING:
        conditions: Manager["IsolationCondition"]
        action: "IsolationAction"

    def conditions_match(self, entry: "Entry") -> bool:
        """Returns True if ALL conditions match the entry (AND logic)."""
        return all(
            c.is_match_for_entry(entry)
            for c in self.conditions.filter(attr__is_active=True)
        )

    def applies_to(self, requesting_entity: Any) -> bool:
        """Returns True if this isolation rule restricts access from requesting_entity."""
        try:
            action = self.action
        except IsolationAction.DoesNotExist:
            return False
        if action.is_prevent_all:
            return True
        return action.prevent_from_id == requesting_entity.id

    def is_entry_isolated(self, entry: "Entry", requesting_entity: Any) -> bool:
        return self.applies_to(requesting_entity) and self.conditions_match(entry)

    @classmethod
    def get_isolated_entry_ids(cls, candidate_entries: "QuerySet", requesting_entity: Any) -> set:
        """
        Returns the set of entry IDs that are isolated from requesting_entity.
        Iterates only IsolationParents whose actions apply to requesting_entity.
        """
        # Collect entity IDs present in the candidate entries
        schema_ids = candidate_entries.values_list("schema_id", flat=True).distinct()

        applicable_parents = (
            cls.objects.filter(entity_id__in=schema_ids)
            .filter(
                models.Q(action__is_prevent_all=True)
                | models.Q(action__prevent_from=requesting_entity)
            )
            .prefetch_related("conditions", "conditions__attr")
        )

        if not applicable_parents.exists():
            return set()

        isolated_ids: set = set()
        for entry in candidate_entries:
            for parent in applicable_parents.filter(entity_id=entry.schema_id):
                if parent.conditions_match(entry):
                    isolated_ids.add(entry.id)
                    break
        return isolated_ids

    def save_conditions(self, conditions_data: list) -> None:
        from entity.models import EntityAttr
        from entry.models import Entry

        for cond_data in conditions_data:
            attr = EntityAttr.objects.filter(
                id=cond_data.get("attr_id"), is_active=True
            ).first()
            if not attr:
                continue

            ref_cond = None
            ref_cond_id = cond_data.get("ref_cond_id")
            if ref_cond_id:
                ref_cond = Entry.objects.filter(id=ref_cond_id).first()

            IsolationCondition.objects.create(
                parent=self,
                attr=attr,
                str_cond=cond_data.get("str_cond") or "",
                ref_cond=ref_cond,
                bool_cond=cond_data.get("bool_cond", False),
                is_unmatch=cond_data.get("is_unmatch", False),
            )

    def clear(self) -> None:
        self.conditions.all().delete()
        try:
            self.action.delete()
        except IsolationAction.DoesNotExist:
            pass


class IsolationCondition(models.Model):
    parent = models.ForeignKey(
        IsolationParent, on_delete=models.CASCADE, related_name="conditions"
    )
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)
    str_cond = models.TextField(blank=True, null=True)
    ref_cond = models.ForeignKey(
        "entry.Entry", on_delete=models.SET_NULL, null=True, blank=True
    )
    bool_cond = models.BooleanField(default=False)
    is_unmatch = models.BooleanField(default=False)

    @property
    def ATTR_TYPE(self) -> AttrType:
        return AttrType(self.attr.type)

    def is_match_for_entry(self, entry: "Entry") -> bool:
        """Check if the entry's current attribute value matches this condition."""
        from entry.models import Attribute

        attr_obj = Attribute.objects.filter(parent_entry=entry, schema=self.attr).first()
        if attr_obj is None:
            result = self._is_empty_condition()
        else:
            attrv = (
                attr_obj.values.filter(is_latest=True, parent_attrv__isnull=True).first()
            )
            if attrv is None:
                result = self._is_empty_condition()
            else:
                result = self._check_attrv(attrv)

        return (not result) if self.is_unmatch else result

    def _is_empty_condition(self) -> bool:
        """Returns True when the condition represents an empty/unset value."""
        try:
            match self.ATTR_TYPE:
                case AttrType.STRING | AttrType.TEXT | AttrType.ARRAY_STRING:
                    return self.str_cond == "" or self.str_cond is None
                case AttrType.OBJECT | AttrType.ARRAY_OBJECT:
                    return self.ref_cond is None
                case AttrType.BOOLEAN:
                    return self.bool_cond is False
                case AttrType.NAMED_OBJECT | AttrType.ARRAY_NAMED_OBJECT:
                    return self.ref_cond is None and (self.str_cond == "" or self.str_cond is None)
        except ValueError:
            pass
        return False

    def _check_attrv(self, attrv: Any) -> bool:
        """Compare a stored AttributeValue against this condition."""
        try:
            match self.ATTR_TYPE:
                case AttrType.STRING | AttrType.TEXT:
                    return attrv.value == self.str_cond

                case AttrType.OBJECT:
                    if self.ref_cond is None:
                        return attrv.referral_id is None
                    return attrv.referral_id == self.ref_cond_id

                case AttrType.BOOLEAN:
                    return attrv.boolean == self.bool_cond

                case AttrType.NAMED_OBJECT:
                    name_match = attrv.value == (self.str_cond or "")
                    if self.ref_cond is None:
                        ref_match = attrv.referral_id is None
                    else:
                        ref_match = attrv.referral_id == self.ref_cond_id
                    return name_match and ref_match

                case AttrType.ARRAY_STRING:
                    children = attrv.data_array.all()
                    if not children.exists():
                        return self.str_cond == "" or self.str_cond is None
                    return any(c.value == self.str_cond for c in children)

                case AttrType.ARRAY_OBJECT:
                    children = attrv.data_array.all()
                    if not children.exists():
                        return self.ref_cond is None
                    if self.ref_cond is None:
                        return False
                    return any(c.referral_id == self.ref_cond_id for c in children)

                case AttrType.ARRAY_NAMED_OBJECT:
                    children = attrv.data_array.all()
                    if not children.exists():
                        return (
                            self.ref_cond is None
                            and (self.str_cond == "" or self.str_cond is None)
                        )
                    for c in children:
                        name_match = c.value == (self.str_cond or "")
                        if self.ref_cond is None:
                            ref_match = c.referral_id is None
                        else:
                            ref_match = c.referral_id == self.ref_cond_id
                        if name_match and ref_match:
                            return True
                    return False

        except (ValueError, AttributeError):
            pass
        return False


class IsolationAction(models.Model):
    parent = models.OneToOneField(
        IsolationParent, on_delete=models.CASCADE, related_name="action"
    )
    prevent_from = models.ForeignKey(
        "entity.Entity",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="isolation_action_targets",
    )
    is_prevent_all = models.BooleanField(default=False)
