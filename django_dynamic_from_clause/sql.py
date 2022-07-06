import django
from django.db import connections
from django.db.models.sql import Query

from django_dynamic_from_clause.compiler import DynamicFormClauseSQLCompiler


class DynamicFormClauseQuery(Query):
    compiler = DynamicFormClauseSQLCompiler

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = None

    def get_compiler(self, using=None, connection=None, elide_empty=True):
        if using is None and connection is None:
            raise ValueError("Need either using or connection")
        if using:
            connection = connections[using]
        if django.VERSION >= (4,):
            return self.compiler(self, connection, using, elide_empty)
        return self.compiler(self, connection, using)
