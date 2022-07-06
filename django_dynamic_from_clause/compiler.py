from django.db.models import Expression
from django.db.models.sql import Query
from django.db.models.sql.compiler import SQLCompiler


class DynamicFormClauseSQLCompiler(SQLCompiler):

    def get_from_clause(self):
        result, params = super().get_from_clause()
        assert self.query.source, "Source must be set before evaluation"
        source_sql, params = self.query.source.as_sql(self, self.connection)

        if isinstance(self.query.source, Query):
            result[0] = f"({source_sql % tuple(params)}) AS {result[0]}"
        elif isinstance(self.query.source, Expression):
            result[0] = f"{source_sql % tuple(params)} AS {result[0]}"
        else:
            raise NotImplementedError("Invalid source type")
        return result, params
