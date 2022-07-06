from django.db import models
from django_dynamic_from_clause.query import DynamicFromClauseQuerySet


class DynamicFromClauseBaseModel(models.Model):
    """
    Require to set source queryset or expression before evaluation.
    In fact, can be evaluated from anything which is QuerySet/Expression, and meet declared interface.
    """
    EXPRESSION_CLASS: None
    objects = DynamicFromClauseQuerySet.as_manager()

    class Meta:
        app_label = ''
        abstract = True
        managed = False
        db_table: str
