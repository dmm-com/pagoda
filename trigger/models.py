from django.db import models


class TriggerParentCondition(models.Model):
    entity = models.ForeignKey("entity.Entity", on_delete=models.CASCADE)


class TriggerCondition(models.Model):
    parent = models.ForeignKey(
        TriggerParentCondition, on_delete=models.CASCADE, related_name="co_condition"
    )
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)
    str_cond = models.TextField()
    ref_cond = models.ForeignKey("entry.Entry", on_delete=models.SET_NULL, null=True, blank=True)
    bool_cond = models.BooleanField(default=False)


class TriggerParentAction(models.Model):
    condition = models.ForeignKey(
        TriggerParentCondition, on_delete=models.CASCADE, related_name="action"
    )


class TriggerAction(models.Model):
    parent = models.ForeignKey(
        TriggerParentAction, on_delete=models.CASCADE, related_name="co_action"
    )
    attr = models.ForeignKey("entity.EntityAttr", on_delete=models.CASCADE)


class TriggerActionValue(models.Model):
    action = models.ForeignKey(TriggerAction, on_delete=models.CASCADE, related_name="values")
    str_cond = models.TextField()
    ref_cond = models.ManyToManyField("entry.Entry", blank=True)
    bool_cond = models.BooleanField(default=False)
