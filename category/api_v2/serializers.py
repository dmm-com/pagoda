from rest_framework import serializers

from category.models import Category
from entity.models import Entity


# We bordered the situation that ID parameter would be readonly via OpenAPI generate
# when EntitySerializer, which is defined in the entity.api_v2.serializers, was specified.
class EntitySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Entity
        fields = ["id", "name", "is_public"]


class CategoryListSerializer(serializers.ModelSerializer):
    models = EntitySerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "note", "models", "priority"]


class CategoryCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    models = EntitySerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "note", "models", "priority"]

    def create(self, validated_data):
        # craete Category instance
        category = Category.objects.create(
            created_user=self.context["request"].user,
            **{k: v for (k, v) in validated_data.items() if k != "models"},
        )

        # make relations created Category with specified Models
        for model in Entity.objects.filter(
            id__in=[x["id"] for x in validated_data.get("models", [])], is_active=True
        ):
            model.categories.add(category)

        return category


class CategoryUpdateSerializer(serializers.ModelSerializer):
    models = EntitySerializer(many=True)

    class Meta:
        model = Category
        fields = ["name", "note", "models", "priority"]

    def update(self, category: Category, validated_data):
        # name and note are updated
        updated_fields: list[str] = []

        for key in ["name", "note", "priority"]:
            content = validated_data.get(key, getattr(category, key))
            if content != getattr(category, key):
                setattr(category, key, content)
                updated_fields.append(key)

        if len(updated_fields) > 0:
            category.save(update_fields=updated_fields)
        else:
            category.save_without_historical_record()

        curr_model_ids = [x.id for x in category.models.filter(is_active=True)]
        new_model_ids = [x["id"] for x in validated_data.get("models", [])]

        # remove models that are unselected from current ones
        removing_model_ids = list(set(curr_model_ids) - set(new_model_ids))
        for model in Entity.objects.filter(id__in=removing_model_ids, is_active=True):
            model.categories.remove(category)

        # add new models that are added to current ones
        adding_model_ids = list(set(new_model_ids) - set(curr_model_ids))
        for model in Entity.objects.filter(id__in=adding_model_ids, is_active=True):
            model.categories.add(category)

        return category
