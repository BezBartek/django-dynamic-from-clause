|  |  |                                                                                                                             |
|--------------------|---------------------|-----------------------------------------------------------------------------------------------------------------------------|
| :memo: | **License** | [![License](https://img.shields.io/:license-mit-blue.svg)](http://doge.mit-license.org)                                     |
| :package: | **PyPi** | [![PyPi](https://badge.fury.io/py/django-dynamic-from-clause.svg)](https://pypi.org/project/django-dynamic-from-clause/)    |
| <img src="https://cdn.iconscout.com/icon/free/png-256/django-1-282754.png" width="22px" height="22px" align="center" /> | **Django Versions** | 2.0, 2.1, 2.2, 3.0, 3.1, 3.2, 4.0, 4.1                                                                                      |
| <img src="http://www.iconarchive.com/download/i73027/cornmanthe3rd/plex/Other-python.ico" width="22px" height="22px" align="center" /> | **Python Versions** | 3.6, 3.7, 3.8, 3.9, 3.10                                                                                                    |

## How to install?

    pip install django-dynamic-from-clause

# **IDEA**
Be able to define the **sql FROM clause** dynamically and fill it with args. 
On django models the sql FROM clause is the db table name or other static name (configured in Meta).

**The idea is to change that!**. By that we are able to map a tabular functions, any sql/queries outputs, and other, to Django models!   
It is what we are trying to do here. 

Anything which have tabular interface output, like: table, view, function, queries, and so on, should be able to map to dedicated django model and be able to use the orm methods  (like select related, prefetch, annotations and others). 

# Examples:
#### Wrap aggregation result
```python
from django.db import models

from django_dynamic_from_clause.models import DynamicFromClauseBaseModel

# regular models
class Owner(models.Model):
    name = models.CharField(max_length=512)


class InventoryRecord(models.Model):
    count = models.IntegerField()
    owner = models.ForeignKey(
        Owner, related_name='inventory_records', on_delete=models.CASCADE
    )


# Our perspective for the InventoryRecordQuerySet
class AggregatedInventoryPerspective(DynamicFromClauseBaseModel):
    count_sum = models.IntegerField()
    owner = models.ForeignKey(
        Owner,
        related_name='+', # Feel free to set the related name and use it. It will work without problems. 
        on_delete=models.DO_NOTHING,
        primary_key=True # We have to pick a field which will mimic the primary key
     )

# Lets make some aggregations
aggr_inv_records_queryset = InventoryRecord.objects.values(
    "owner"
).annotate(
    count_sum=models.Sum("count")
)
# Generated SQL is: 
# 'SELECT "test_app_inventoryrecord"."owner_id", SUM("test_app_inventoryrecord"."count") AS "count_sum" 
# FROM "test_app_inventoryrecord" 
# GROUP BY "test_app_inventoryrecord"."owner_id"'
#
# And example output is: <QuerySet [{'owner': 36, 'count_sum': 24}]>


# Let use ORM on the results from the aggr_inv_records_queryset
aggregated_inv_records = AggregatedInventoryPerspective.objects.set_source_from_queryset(
    aggr_inv_records_queryset
).select_related('owner')

# Generated SQL is:
# SELECT 
#   "_aggregatedinventoryperspective"."count_sum", 
#   "_aggregatedinventoryperspective"."owner_id",
#   "test_app_owner"."id", "test_app_owner"."name" 
# FROM (
#    SELECT "test_app_inventoryrecord"."owner_id", SUM("test_app_inventoryrecord"."count") AS "count_sum" 
#    FROM "test_app_inventoryrecord" 
#    GROUP BY "test_app_inventoryrecord"."owner_id") AS "_aggregatedinventoryperspective" 
#    INNER JOIN "test_app_owner" ON ("_aggregatedinventoryperspective"."owner_id" = "test_app_owner"."id"
)
# and example output is: 
#   <DynamicFromClauseQuerySet [<AggregatedInventoryPerspective: AggregatedInventoryPerspective object (36)>]>
aggregated_inv_records.get().owner  # return an owner :), Our perspective can be prefetched from the Owner model as well.

```

#### Filter trough results of the window annotation on same queryset
```python
from django.db import models
from django.db.models import QuerySet
from django.db.models import F, Window
from django.db.models.functions import Rank

from django_dynamic_from_clause.query import DynamicFromClauseQuerySet

# Regular django model, with extra objects manager 
class Human(models.Model):
    objects = QuerySet.as_manager()
    dynamic_from_clause_objects = DynamicFromClauseQuerySet.as_manager()
    weight = models.IntegerField()
    height = models.IntegerField()

# We would like to annotate rank, and filter through it, 
# which is imposible in regular django without raw query. 
# Django will throw NotSupportedError
humans_with_rank = Human.objects.all().annotate(rank=Window(
    expression=Rank(),
    order_by=[F('height'), F('weight')]
))

# But we can easily overcome that!
# By using our manager, to make query from the query
humans_with_rank_less_or_equal_two = Human.dynamic_from_clause_objects.set_source_from_queryset(
    humans_with_rank, forward_fields=['rank']
).get(rank__lte=2)
# Let's see how generated query looks like:
# SELECT 
#   "test_app_human"."id", "test_app_human"."weight",
#   "test_app_human"."height", "test_app_human"."rank" AS "rank" 
# FROM (
#   SELECT 
#       "test_app_human"."id",
#       "test_app_human"."weight", 
#       "test_app_human"."height",
#       RANK() OVER (ORDER BY "test_app_human"."height", "test_app_human"."weight") AS "rank" 
#   FROM "test_app_human"
# ) AS "test_app_human" 
# WHERE "test_app_human"."rank" <= 2
# And we still deal with a Human objects!
# <DynamicFromClauseQuerySet [<Human: Human object (218)>, <Human: Human object (216)>]>
```

#### Let's use some database functions - check which rows are lock-ed on provided table
```python
from django.db import models
from django.db.models import Func
from django.contrib.postgres.fields import ArrayField

from django_dynamic_from_clause.models import DynamicFromClauseBaseModel


class ExampleModel(models.Model):
    pass


class PGRowLocks(Func):  # you have to create pgrowlock extension first
    function = 'pgrowlocks'
    template = "%(function)s('%(expressions)s')"


# This model maps to the pgrowslocks function output which is all locks on provided table
class PgRowsLocks(DynamicFromClauseBaseModel):
    EXPRESSION_CLASS = PGRowLocks 

    locked_row = ArrayField(models.PositiveIntegerField(), size=2, primary_key=True)
    locker = models.PositiveBigIntegerField()
    multi = models.BooleanField()
    xids = ArrayField(models.PositiveIntegerField())
    modes = models.PositiveIntegerField(models.TextField())
    pids = ArrayField(models.SmallIntegerField())

# Now we can easy check what is locked on which table :)
locked_rows = PgRowsLocks.objects.fill_expression_with_parameters(
        ExampleModel._meta.db_table
).all()    
```
#### My tabular function
`
cooming soon, for now check tests
`

## Note:
We have to specify which field is the primary key on the model 

# How it works?

The Code is easy. The only thing which we do here is to extend the django SQL compiler and change how it creates the from_clause. The library has very little code.

# Motivation

I think that this approach has sense cus I saw a lot of problems or ugly solutions which have tried to:   
* use table functions,  
* serialize objects on aggregated queryset,  
* make selects over nested queries,  
* replacing what database should do with python code,   
* "manually" prefetching on serializers lvl, 
* and others ugly things.

I think that this library contains a good idea, and a reasonable attempt, to solve issues like the above.

# TODO:
- Migrations (here or in other library like the django-db-views - db functions can be a good replacement for views, cus views always calculate the whole dataset which can raise performance issues). 

# How to work with repo
add your .env file in the main directory, which set up POSTGRES env variables. Check conftest.py file for more details.
