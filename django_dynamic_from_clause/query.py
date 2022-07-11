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

    def _forward_annotation(self, fields: List['str'], source: Query, target: QuerySet) -> QuerySet:
        for forward_field in fields:
            assert source.annotations[forward_field], "Only annotated fields can be put in the forward fields list."
            annotated_field = source.annotations[forward_field].field.__class__()
            setattr(annotated_field, 'column', forward_field)
            target = target.annotate(**{forward_field: Col(self.model._meta.db_table, annotated_field)})
        return target

    def set_source(
            self, source: Union[Query, Expression], annotated_fields_to_forward: List[str] = None
    ) -> 'DynamicFromClauseQuerySet':
        """
        :param source: Source can be expression or queryset.
        :param annotated_fields_to_forward: Fields which have to be pass up from the source query.
                                            Works only with queries
        """
        clone = self._chain()
        clone.query.source = source
        if annotated_fields_to_forward:
            assert isinstance(source, Query), "annotated_fields_to_forward parameter is supported only for queryset source."
            clone = self._forward_annotation(annotated_fields_to_forward, source, clone)
        elif isinstance(source, Query) and source.model is clone.model:
            clone = self._forward_annotation(source.annotations.keys(), source, clone)
        return clone

    def set_source_from_queryset(
            self, queryset: QuerySet, annotated_fields_to_forward: list = None
    ) -> 'DynamicFromClauseQuerySet':
        return self.set_source(queryset.query, annotated_fields_to_forward)

    def set_source_from_expression(
            self, expression_class: Type[Expression], *args
    ) -> 'DynamicFromClauseQuerySet':
        expression = expression_class(*(models.Value(arg) for arg in args))
        return self.set_source(expression, annotated_fields_to_forward=[])

    def fill_expression_with_parameters(self, *args) -> 'DynamicFromClauseQuerySet':
        """Uses default Expression class from model."""
        assert self.model.EXPRESSION_CLASS, \
            "This method uses statically declared expression class from model. " \
            "please use set_source_from_expression and provide explicitly an expression class or set it on the model."
        return self.set_source_from_expression(self.model.EXPRESSION_CLASS, *args)
