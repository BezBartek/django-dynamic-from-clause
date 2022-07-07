from typing import Union, Type, List

from django.db import models
from django.db.models import QuerySet, Expression
from django.db.models.expressions import Col
from django.db.models.sql import Query

from django_dynamic_from_clause.sql import DynamicFormClauseQuery


class DynamicFromClauseQuerySet(QuerySet):
    def __init__(self, model=None, query=None, using=None, hints=None):
        if query:
            assert isinstance(query, DynamicFormClauseQuery), f'Provided query: {query}'
        query = query or DynamicFormClauseQuery(model)
        super().__init__(model=model, query=query, using=using, hints=hints)

    def set_source(self, source: Union[Query, Expression], forward_fields: List[str]) -> 'DynamicFromClauseQuerySet':
        """
        :param source: Source can be expression or queryset.
        :param forward_fields: Fields which have to be pass up from the source query. Works only with queries
        """
        clone = self._chain()
        clone.query.source = source
        if forward_fields:
            assert isinstance(source, Query), "forward_fields parameter is supported only for queryset source."
            for forward_field in forward_fields:
                assert source.annotations[forward_field], "Only annotated fields can be put in the forward fields list."
                target = source.annotations[forward_field].field.__class__()
                setattr(target, 'column', forward_field)
                clone = clone.annotate(**{forward_field: Col(self.model._meta.db_table, target)})
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
