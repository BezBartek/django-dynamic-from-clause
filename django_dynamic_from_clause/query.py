from typing import Union, Type

from django.db import models
from django.db.models import QuerySet, Expression
from django.db.models.sql import Query

from django_dynamic_from_clause.sql import DynamicFormClauseQuery


class DynamicFromClauseQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if query:
            assert isinstance(query, DynamicFormClauseQuery), f'Provided query: {query}'
        query = query or DynamicFormClauseQuery(model)
        super().__init__(model=model, query=query, using=using, hints=hints)

    def set_source(self, source: Union[Query, Expression], forward_fields: list) -> 'DynamicFromClauseQuerySet':
        clone = self._chain()
        clone.query.source = source
        if forward_fields:
            clone = clone.extra(
                select={
                    forward_field: f'{self.model._meta.db_table}.{forward_field}' for forward_field in forward_fields
                }
            )
        return clone

    def set_source_from_queryset(self, queryset: QuerySet, forward_fields: list = None) -> 'DynamicFromClauseQuerySet':
        return self.set_source(queryset.query, forward_fields or [])

    def set_source_from_expression(self, expression_class: Type[Expression], *args) -> 'DynamicFromClauseQuerySet':
        expression = expression_class(*(models.Value(arg) for arg in args))
        return self.set_source(expression, forward_fields=[])

    def fill_expression_with_parameters(self, *args) -> 'DynamicFromClauseQuerySet':
        """Uses default Expression class from model."""
        assert self.model.EXPRESSION_CLASS, \
            "This method uses statically declared expression class from model. " \
            "please use set_source_from_expression and provide explicitly an expression class or set it on the model."
        return self.set_source_from_expression(self.model.EXPRESSION_CLASS, *args)
