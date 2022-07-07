WORK IN PROGRESS, 
LIB IS ON INITIAL STATE,
CONSIDER BEFORE HEAVY USAGE


# **IDEA**

Be able to define the **sql FROM clause** dynamically and fill it with args. 
On django models the sql FROM clause is the db table name or other static name (configured in Meta).

**The idea is to change that!**. By that we are able to map a tabular functions, any sql/queries outputs, and other, to Django models!   
It is what we are trying to do here. 

Anything which have tabular interface output, like: table, view, function, queries, and so on, should be able to map to dedicated django model and be able to use the orm methods  (like select related, prefetch, annotations and others). 

# Examples:
### Bases on query
#### Aggregation
```
# regular models
class Owner(models.Model):
    name = models.CharField(max_length=512)


class InventoryRecord(models.Model):
    count = models.IntegerField()
    owner = models.ForeignKey(Owner, related_name='inventory_records', on_delete=models.CASCADE)


# Our perspective for the InventoryRecordQuerySet
class AggregatedInventoryPerspective(DynamicFromClauseBaseModel):
    count_sum = models.IntegerField()
    owner = models.ForeignKey(Owner, related_name='+', on_delete=models.DO_NOTHING, primary_key=True)

# Lets make some aggregations
aggr_inv_records_queryset = InventoryRecord.objects.values("owner").annotate(count_sum=models.Sum("count"))

# Let use ORM on the results from the aggr_inv_records_queryset
aggregated_inv_records = AggregatedInventoryPerspective.objects.set_source_from_queryset(
    aggr_inv_records_queryset
).select_related('owner')
```

#### Window on same queryset
```
# Regular django model, with extra objects manager 
class Human(models.Model):
    objects = QuerySet.as_manager()
    dynamic_from_clause_objects = DynamicFromClauseQuerySet.as_manager()
    weight = models.IntegerField()
    height = models.IntegerField()

# We would like to annotate rank, and filter trought it, 
# which is imposible in regular django without raw query. 
# we can easy solve it here:

humans_with_rank = Human.objects.all().annotate(rank=Window(
    expression=Rank(),
    order_by=[F('height'), F('weight')]
))

# Now we can use our manager, to make query from the query
human_with_rank_equal_two = Human.dynamic_from_clause_objects.set_source_from_queryset(
    humans_with_rank, forward_fields=['rank']
).filter(rank=2)
```

### Bases on some tablear function
#### My tabular function
`
cooming soon, for now check tests
`

#### Let's check what is lock-ed on my table 
`
cooming soon, for now check tests
`

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
- In the case when we forward not declared fields from nested queryset to the parent, we should be able to filter through them not by using extra.
- Add tests across multiple django versions
- Migrations (here or in other library like the django-db-views - db functions can be a good replacement for views, cus views always calculate the whole dataset which can raise performance issues). 


# How to work with repo
add your .env file in the main directory, which set up POSTGRES env variables. See conftest.py file.