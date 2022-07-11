import pytest
from django.db import models, connections
from django.db.models import Func, F, Window
from django.db.models.functions import Rank

from tests.test_app.models import InventoryRecord, Owner, AggregatedInventoryPerspective, PgBlockingPidsModel, \
    PgBackendPid, InvRecordTableFunctionModel, Human


@pytest.mark.django_db
def test_execute_from_queryset():
    owner = Owner.objects.create(name='Kratos')
    InventoryRecord.objects.create(count=12, owner=owner)
    InventoryRecord.objects.create(count=12, owner=owner)

    aggr_inv_records_queryset = InventoryRecord.objects.values(
        "owner"
    ).annotate(
        count_sum=models.Sum("count")
    )

    aggregated_inv_records = AggregatedInventoryPerspective.objects.set_source_from_queryset(
        aggr_inv_records_queryset
    ).select_related('owner')

    assert len(aggregated_inv_records) == 1
    agg_in_rec = aggregated_inv_records[0]
    assert agg_in_rec.owner == owner
    assert agg_in_rec.count_sum == 24


@pytest.mark.django_db
def test_execution_on_same_model_which_using_manager_only_with_annotated_fields_to_forward():
    """
    Check the Human model. He has declared two managers. Regular one and the dynamic from clause manager.
    Human is a regular django model.
    """
    expected_human_with_rank_2 = Human.objects.create(height=177, weight=88)
    Human.objects.create(height=177, weight=92)
    Human.objects.create(height=134, weight=50)

    humans_with_rank = Human.objects.all().annotate(rank=Window(
        expression=Rank(),
        order_by=[F('height'), F('weight')]
    ))

    humans_with_rank_2 = Human.dynamic_from_clause_objects.set_source_from_queryset(
        humans_with_rank, annotated_fields_to_forward=['rank']
    ).filter(rank=2)
    assert len(humans_with_rank_2) == 1
    assert humans_with_rank_2[0] == expected_human_with_rank_2
    assert humans_with_rank_2[0].rank == 2


@pytest.mark.django_db
def test_execution_on_same_model_which_using_manager_only_annotated_fields_to_forward_not_provided():
    expected_human_with_rank_2 = Human.objects.create(height=177, weight=88)
    Human.objects.create(height=177, weight=92)
    Human.objects.create(height=134, weight=50)

    humans_with_rank = Human.objects.all().annotate(rank=Window(
        expression=Rank(),
        order_by=[F('height'), F('weight')]
    )).annotate(height_and_weight=F('height') * F('weight'))

    humans_with_rank_2 = Human.dynamic_from_clause_objects.set_source_from_queryset(
        humans_with_rank
    ).filter(rank=2)
    assert len(humans_with_rank_2) == 1
    human_with_rank_2 = humans_with_rank_2[0]
    assert human_with_rank_2 == expected_human_with_rank_2
    assert human_with_rank_2.rank == 2
    assert human_with_rank_2.height_and_weight


@pytest.mark.django_db
def test_execute_from_single_value_postgres_function():
    class PgBackendPidFunc(Func):
        function = 'pg_backend_pid'
        template = "%(function)s(%(expressions)s)"
        arity = 0

    class PgBlockingPidsFunc(Func):
        """Only for postgres and require an extension"""
        function = 'pg_blocking_pids'
        template = "%(function)s(%(expressions)s)"
        arity = 1

    my_pid = PgBackendPid.objects.set_source_from_expression(PgBackendPidFunc).get()
    blocking_pids = PgBlockingPidsModel.objects.set_source_from_expression(
        PgBlockingPidsFunc, my_pid._pgbackendpid
    ).all()
    assert blocking_pids[0]


@pytest.mark.django_db
def test_uses_expression_declared_on_model_lvl():
    my_pid = PgBackendPid.objects.fill_expression_with_parameters().get()
    assert my_pid._pgbackendpid


@pytest.mark.django_db
def test_execute_from_table_function():
    owner = Owner.objects.create(name='Kratos')
    inv_record = InventoryRecord.objects.create(count=12, owner=owner)

    cursor = connections['default'].cursor()
    cursor.execute(
        '''
        CREATE OR REPLACE FUNCTION get_inventory(int) RETURNS setof test_app_inventoryrecord AS '
            SELECT * FROM test_app_inventoryrecord WHERE id = $1;
        ' LANGUAGE SQL;
        '''
    )

    class PgBackendPidFunc(Func):
        function = 'get_inventory'
        template = "%(function)s(%(expressions)s)"
        arity = 1

    func_output = InvRecordTableFunctionModel.objects.set_source_from_expression(
        PgBackendPidFunc, inv_record.id
    ).get()
    assert func_output.id == inv_record.id
