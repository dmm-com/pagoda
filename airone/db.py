class SpannerRouter:
    """
    A router to control all database operations on models using Spanner.
    """

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'entry' and model.__name__ == 'AdvancedSearchAttributeIndex':
            return 'spanner'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'entry' and model.__name__ == 'AdvancedSearchAttributeIndex':
            return 'spanner'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between models in the same database
        if obj1._state.db == obj2._state.db:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'spanner':
            # Only allow AdvancedSearchAttributeIndex model to be migrated to Spanner
            return (app_label == 'entry' and model_name == 'advancedsearchattributeindex')
        elif app_label == 'entry' and model_name == 'advancedsearchattributeindex':
            # Prevent AdvancedSearchAttributeIndex from being migrated to other databases
            return False
        return None 