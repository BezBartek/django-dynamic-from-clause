from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import QuerySet, Func

from django_dynamic_from_clause.models import DynamicFromClauseBaseModel


# Example models
from django_dynamic_from_clause.query import DynamicFromClauseQuerySet


class Owner(models.Model):
    name = models.CharField(max_length=512)


class InventoryRecord(models.Model):
    count = models.IntegerField()
    owner = models.ForeignKey(Owner, related_name='inventory_records', on_delete=models.CASCADE)


# regular table which using Dynamic Manager
class Human(models.Model):
    objects = QuerySet.as_manager()
    dynamic_from_clause_objects = DynamicFromClauseQuerySet.as_manager()
    weight = models.IntegerField()
    height = models.IntegerField()


# Example perspectives for QuerySets
class AggregatedInventoryPerspective(DynamicFromClauseBaseModel):
    count_sum = models.IntegerField()
    owner = models.ForeignKey(Owner, related_name='+', on_delete=models.DO_NOTHING, primary_key=True)


# Already declared Table function
class InvRecordTableFunctionModel(DynamicFromClauseBaseModel):
    id = models.IntegerField(InventoryRecord, primary_key=True)


# Example functions which returns single value
class PgBackendPidFunc(Func):
    function = 'pg_backend_pid'
    template = "%(function)s(%(expressions)s)"
    arity = 0


class PgBackendPid(DynamicFromClauseBaseModel):
    EXPRESSION_CLASS = PgBackendPidFunc
    _pgbackendpid = models.IntegerField(primary_key=True)


class PgBlockingPidsModel(DynamicFromClauseBaseModel):
    _pgblockingpidsmodel = ArrayField(base_field=models.IntegerField(), primary_key=True)

