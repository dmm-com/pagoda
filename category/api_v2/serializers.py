from rest_framework import serializers

from category.models import Category
from entity.api_v2.serializers import EntitySerializer
from entity.models import Entity


class CategoryListSerializer(serializers.ModelSerializer):
    models = EntitySerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "name", "note", "models"]


class CategoryCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False, read_only=True)
    models = serializers.ListField(write_only=True, required=False, default=[])

    class Meta:
        model = Category
        fields = ["id", "name", "note", "models"]

    def create(self, validated_data):
        # craete Category instance
        category = Category.objects.create(
            created_user=self.context["request"].user,
            **{k: v for (k, v) in validated_data.items() if k != "models"},
        )

        # make relations created Category with specified Models
        for model in Entity.objects.filter(id__in=validated_data.get("models", []), is_active=True):
            model.categories.add(category)

        return category


class CategoryUpdateSerializer(serializers.ModelSerializer):
    models = serializers.ListField(write_only=True, required=False, default=[])

    class Meta:
        model = Category
        fields = ["name", "note", "models"]

    def update(self, category: Category, validated_data):
        curr_model_ids = [x.id for x in category.models.filter(is_active=True)]

        # remove models that are unselected from current ones
        removing_model_ids = list(
            set(curr_model_ids) - set(validated_data.get("models", curr_model_ids))
        )
        for model in Entity.objects.filter(id__in=removing_model_ids, is_active=True):
            model.categories.remove(category)

        # add new models that are added to current ones
        adding_model_ids = list(
            set(validated_data.get("models", curr_model_ids)) - set(curr_model_ids)
        )
        for model in Entity.objects.filter(id__in=adding_model_ids, is_active=True):
            model.categories.add(category)

        return category
