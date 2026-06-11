from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import final, overload



from WinCopies import IInterface, IDisposable, Abstract

from WinCopies.Collections import EnumerationOrder
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Abstraction.Collection.Mapping import Dictionary
from WinCopies.Collections.Abstraction.Enumeration import CreateCountableEnumerable
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IEnumerator, Enumerable, TryGetEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursivelyEnumerable, DefaultRecursiveStackedEnumerator
from WinCopies.Collections.Extensions import ICollection, IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked.Singly import IList, ICountableEnumerableList, Queue, CountableQueue, CountableEnumerableQueue

from WinCopies.Enum import HasFlag

from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Object import IValueItem, IString, String
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult, DualValueBool



from WinCopies.Data import QueryErrorKinds, Ordering, IColumn
from WinCopies.Data.Misc import IQueryBase
from WinCopies.Data.Parameter import IFormattable
from WinCopies.Data.QueryBuilder import QueryResult, IConditionalQueryBuilder, ISelectionQueryBuilder, ConditionalQueryBuilder, SelectionQueryBuilder, GetPrefixedSelectionQueryWriter
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet, IBranchSet, IJoin, TableParameterSet

class IQueryLimits(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetMaxParameterCount(self) -> DualValueBool[int]|None:
        ...

    @abstractmethod
    def GetMaxQuerySize(self) -> int|None:
        ...
class IMutableQueryLimits(IQueryLimits):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def UpdateParameterCount(self, size: int, safe: bool) -> bool|None:
        ...

class IQueryExecutionResult(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetRowCount(self) -> int:
        ...

class ISelectionQueryExecutionResult(IEnumerable[Sequence[object]], IQueryExecutionResult):
    def __init__(self) -> None: super().__init__()
class IInsertionQueryExecutionResult(IQueryExecutionResult):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetLastRowId(self) -> int:
        ...

class IQuery[TQueryResult, TQueryExecutionResult: IQueryExecutionResult|None](IQueryBase[TQueryResult]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def Execute(self, guards: None = None) -> TQueryExecutionResult:
        ...
    @overload
    def Execute(self, guards: QueryErrorKinds) -> TQueryExecutionResult|QueryErrorKinds:
        ...

    @abstractmethod
    def Execute(self, guards: QueryErrorKinds|None = None) -> TQueryExecutionResult|QueryErrorKinds:
        ...

class QueryProvider[T](Abstract, IQueryBase[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _Validate(self) -> str|None:
        ...
class QueryExceptionMapper(Abstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _TryMapException(self, exception: Exception) -> QueryErrorKinds:
        ...
class QueryBase[TQueryResult, TQueryExecutionResult: IQueryExecutionResult|None](QueryProvider[TQueryResult], QueryExceptionMapper, IQuery[TQueryResult, TQueryExecutionResult]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetQueryOverride(self) -> TQueryResult:
        ...

    def GetQuery(self) -> TQueryResult:
        result: str|None = self._Validate()
        
        if result is None: return self._GetQueryOverride()
        
        raise InvalidOperationError(result)
    
    @abstractmethod
    def _Execute(self) -> TQueryExecutionResult:
        ...
    
    @overload
    def Execute(self, guards: None = None) -> TQueryExecutionResult:
        ...
    @overload
    def Execute(self, guards: QueryErrorKinds) -> TQueryExecutionResult|QueryErrorKinds:
        ...
    
    @final
    def Execute(self, guards: QueryErrorKinds|None = None) -> TQueryExecutionResult|QueryErrorKinds:
        def check(guards: QueryErrorKinds) -> bool: return guards == QueryErrorKinds.Null

        try: return self._Execute()
        
        except Exception as e:
            if guards is None or check(guards): raise

            _guards: QueryErrorKinds = self._TryMapException(e)

            if check(_guards) or not HasFlag(guards, _guards): raise
            
            return _guards
class Query[T: IQueryExecutionResult](QueryBase[QueryResult, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetQuery(self) -> QueryResult: return super().GetQuery()

class INullableQueryBase(IQueryBase[QueryResult|None]):
    def __init__(self) -> None: super().__init__()
class INullableQuery[T: IQueryExecutionResult](INullableQueryBase, IQuery[QueryResult|None, T|None]):
    def __init__(self) -> None: super().__init__()

class NullableQueryProvider(QueryProvider[QueryResult|None]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _Prevalidate(self) -> bool:
        ...
class NullableQuery[T: IQueryExecutionResult](NullableQueryProvider, QueryBase[QueryResult|None, T|None], INullableQuery[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetQuery(self) -> QueryResult|None: return super().GetQuery() if self._Prevalidate() else None

class IConditionalQuery(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        ...

class ISelectionQueryBase(IConditionalQuery):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetTables(self) -> ITableParameterSet:
        ...
    
    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        ...
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        ...

    @abstractmethod
    def GetSubqueries(self) -> IEnumerable[ISubselectionQuery]|None:
        ...
    @abstractmethod
    def SetSubqueries(self, subqueries: IEnumerable[ISubselectionQuery]|None) -> None:
        ...

class ISelectionQuery(ISelectionQueryBase, INullableQuery[ISelectionQueryExecutionResult]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> IColumnParameterSet[IFormattable]:
        ...

    @abstractmethod
    def GetJoins(self) -> ICollection[IJoin]:
        ...
    @abstractmethod
    def GetCases(self) -> ICollection[IBranchSet[IValueItem]]:
        ...
    @abstractmethod
    def GetOrdering(self) -> IDictionary[IColumn, Ordering]:
        ...
class ISubselectionQuery(ISelectionQueryBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IKeyValuePair[IColumn, IFormattable]:
        ...

class IWriteQuery(IQuery[QueryResult, IInsertionQueryExecutionResult]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        ...

class IInsertionQueryBase[T](IWriteQuery):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetItems(self) -> T:
        ...

class IInsertionQuery(IInsertionQueryBase[IDictionary[IString, object]]):
    def __init__(self) -> None: super().__init__()
class IMultiInsertionQuery(IInsertionQueryBase[Iterable[Iterable[object]]]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> ICountableEnumerable[IString]:
        ...

class IUpdateQuery(IWriteQuery, IConditionalQuery):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValues(self) -> IDictionary[IString, object]:
        ...

class SelectionQueryBase(Abstract, ISelectionQueryBase):
    def __init__(self, tables: ITableParameterSet|str, conditions: IConditionParameterSet|None, subqueries: IEnumerable[ISubselectionQuery]|None = None) -> None:
        super().__init__()
    
        self.__tables: ITableParameterSet = tables if isinstance(tables, ITableParameterSet) else TableParameterSet.CreateFromNames(String(tables))
        self.__conditions: IConditionParameterSet|None = conditions
        self.__subqueries: IEnumerable[ISubselectionQuery]|None = subqueries
    
    @final
    def _PrevalidateQuery(self, query: ISelectionQueryBase) -> bool:
        return query.GetTables().GetCount() > 0
    @final
    def _Prevalidate(self) -> bool:
        return self._PrevalidateQuery(self)
    
    @final
    def GetTables(self) -> ITableParameterSet: return self.__tables
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None: return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None: self.__conditions = conditions
    
    @final
    def GetSubqueries(self) -> IEnumerable[ISubselectionQuery]|None: return self.__subqueries
    @final
    def SetSubqueries(self, subqueries: IEnumerable[ISubselectionQuery]|None) -> None: self.__subqueries = subqueries
class SelectionQuery(SelectionQueryBase, NullableQuery[ISelectionQueryExecutionResult], ISelectionQuery):
    @final
    class __Enumerable(RecursivelyEnumerable[ISubselectionQuery]):
        @final
        class __EnumerableSelectionQuery(Enumerable[ISubselectionQuery]):
            def __init__(self, query: ISubselectionQuery) -> None:
                super().__init__()

                self.__query: ISubselectionQuery = query
            
            def TryGetEnumerator(self) -> IEnumerator[ISubselectionQuery]|None: return TryGetEnumerator(self.__query.GetSubqueries())
        
        @final
        class __Enumerator(DefaultRecursiveStackedEnumerator[ISubselectionQuery]):
            def __init__(self, enumerable: RecursivelyEnumerable[ISubselectionQuery], enumerator: IEnumerator[ISubselectionQuery], converter: Converter[ISubselectionQuery, IEnumerable[ISubselectionQuery]], queryBuilder: ISelectionQueryBuilder) -> None:
                super().__init__(enumerable, enumerator, converter)

                self.__queryBuilder: ISelectionQueryBuilder = queryBuilder
            
            def __Write(self, value: str) -> None:
                self.__queryBuilder.Write(value)
            
            def _OnEnteringMainLevel(self, item: ISubselectionQuery) -> bool:
                self.__Write(', ')
                
                return True
            
            def _OnEnteringLevel(self, item: ISubselectionQuery) -> None: self.__Write('(')
            
            def _OnExitingLevel(self, cookie: ISubselectionQuery) -> None:
                self.__queryBuilder.AddConditions(cookie.GetConditions())
                self.__Write(')')
        
        def __init__(self, queries: IEnumerable[ISubselectionQuery], queryBuilder: ISelectionQueryBuilder) -> None:
            super().__init__()

            self.__queries: IEnumerable[ISubselectionQuery] = queries
            self.__queryBuilder: ISelectionQueryBuilder = queryBuilder
        
        def _AsRecursivelyEnumerable(self, container: ISubselectionQuery) -> IEnumerable[ISubselectionQuery]: return SelectionQuery.__Enumerable.__EnumerableSelectionQuery(container)
        
        def _TryGetRecursiveStackedEnumerator(self, enumerator: IEnumerator[ISubselectionQuery], enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[ISubselectionQuery]|None = None) -> IEnumerator[ISubselectionQuery]|None: return SelectionQuery.__Enumerable.__Enumerator(self, enumerator, self._AsRecursivelyEnumerable, self.__queryBuilder)
        def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[ISubselectionQuery], handler: IRecursiveEnumerationHandler[ISubselectionQuery]|None = None) -> IEnumerator[ISubselectionQuery]|None: return self._TryGetRecursiveStackedEnumerator(enumerator)
        
        def TryGetEnumerator(self) -> IEnumerator[ISubselectionQuery]|None: return self.__queries.TryGetEnumerator()
    
    def __init__(self, tables: ITableParameterSet|str, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None) -> None:
        super().__init__(tables, conditions)

        self.__cases: ICollection[IBranchSet[IValueItem]] = List[IBranchSet[IValueItem]]()
        self.__joins: ICollection[IJoin] = List[IJoin]()
        self.__ordering: IDictionary[IColumn, Ordering] = Dictionary[IColumn, Ordering]()
        self.__columns: IColumnParameterSet[IFormattable] = columns
    
    @final
    def GetColumns(self) -> IColumnParameterSet[IFormattable]: return self.__columns

    @final
    def GetJoins(self) -> ICollection[IJoin]: return self.__joins
    @final
    def GetCases(self) -> ICollection[IBranchSet[IValueItem]]: return self.__cases
    @final
    def GetOrdering(self) -> IDictionary[IColumn, Ordering]: return self.__ordering
    
    @final
    def _GetQueryOverride(self) -> QueryResult|None:
        def getTables(query: ISelectionQueryBase) -> str:
            """
            Retrieves the tables and routine calls for a given query.

            Parameters:
            - query: The query to retrieve the tables and routine calls from.

            Returns:
            The concatenated SQL formatted tables and routine calls with their alias.
            """
            
            return queryBuilder.Join(queryBuilder.AddTable(table.GetKey().ToString(), table.GetValue()) for table in query.GetTables().AsIterable())
        
        def initQuery() -> bool:
            """
            Tries to build the beginning of the SQL query from the current query representation.

            Returns:
            A boolean value indicating whether the query building initialization FAILED (for optimization reason).
            """
            def getColumns() -> str: return queryBuilder.Join(queryBuilder.ProcessColumns(self.GetColumns()))
            
            def getSubqueries() -> bool:
                """
                Parses the subqueries of the current main query and adds the result to the memory stream and the arguments to the query argument list.

                Returns:
                A boolean value indicating whether the query building initialization FAILED (for optimization reason).
                """
                subqueries: IEnumerable[ISubselectionQuery]|None = self.GetSubqueries()

                if subqueries is None: return False # No subquery; continue query building.
                
                column: IKeyValuePair[IColumn, IFormattable]|None = None
                
                for query in SelectionQuery.__Enumerable(subqueries, queryBuilder).AsIterable():
                    if not self._PrevalidateQuery(query): return True # A subquery failed to validate; cancel query building.
                    
                    column = query.GetColumn()
                    
                    queryBuilder.Write(f"SELECT {queryBuilder.ProcessConditionValue(column.GetKey(), column.GetValue())} FROM {getTables(query)}")
                
                return False # Process succeeded; continue query building.
            
            def addCases() -> None:
                for case in self.GetCases().AsIterable(): case.Render(GetPrefixedSelectionQueryWriter(', ', queryBuilder))
            
            queryBuilder.Write(f"SELECT {getColumns()}")

            addCases()

            if getSubqueries(): return True # Cancel query building.
            
            queryBuilder.Write(f" FROM {getTables(self)}")

            queryBuilder.AddJoins(self.GetJoins().AsIterable())

            return False # Continue query rendering.
        
        with (queryBuilder := SelectionQueryBuilder(self)):
            queryBuilder.OpenStream()

            if initQuery(): return None
            
            queryBuilder.AddConditions(self.GetConditions())
            
            return queryBuilder.Build()
class SubselectionQuery(SelectionQueryBase, ISubselectionQuery):
    def __init__(self, tables: ITableParameterSet, column: IKeyValuePair[IColumn, IFormattable], conditions: IConditionParameterSet|None, subqueries: IEnumerable[ISubselectionQuery]|None = None) -> None:
        super().__init__(tables, conditions, subqueries)

        self.__column: IKeyValuePair[IColumn, IFormattable] = column
    
    @final
    def GetColumn(self) -> IKeyValuePair[IColumn, IFormattable]: return self.__column

class WriteQuery(Query[IInsertionQueryExecutionResult], IWriteQuery):
    def __init__(self, tableName: str) -> None:
        super().__init__()

        self.__tableName: str = tableName
    
    @final
    def GetTableName(self) -> str: return self.__tableName
    @final
    def GetFormattedTableName(self) -> str: return self.FormatTableName(self.GetTableName())

class InsertionQueryStatementProvider(Abstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetStatement(self, ignoreExisting: bool = False) -> str:
        ...
class InsertionQueryBase[T](WriteQuery, IInsertionQueryBase[T], InsertionQueryStatementProvider):
    def __init__(self, tableName: str, items: T, ignoreExisting: bool = False) -> None:
        super().__init__(tableName)

        self.__items: T = items
        self.__ignoreExisting: bool = ignoreExisting
    
    @final
    def GetItems(self) -> T: return self.__items
    
    @final
    def IgnoreExisting(self) -> bool: return self.__ignoreExisting

class InsertionQuery(InsertionQueryBase[IDictionary[IString, object]], IInsertionQuery):
    def __init__(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> None: super().__init__(tableName, items, ignoreExisting)
    
    @staticmethod
    def __GetStatement(onExisting: str) -> str:
        return f"INSERT{onExisting} INTO"
    
    @staticmethod
    def GetStandardStatement(ignoreExisting: bool = False) -> str:
        return InsertionQuery.__GetStatement(" OR IGNORE" if ignoreExisting else '')
    @staticmethod
    def GetConciseStatement(ignoreExisting: bool = False) -> str:
        return InsertionQuery.__GetStatement(" IGNORE" if ignoreExisting else '')
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        args: ICountableEnumerableList[object] = CountableEnumerableQueue[object]()

        def getValues() -> DualResult[str, str]:
            def join(values: Iterable[str]) -> str: return ", ".join(values)

            columns: IList[str] = Queue[str]()

            def addValue(item: IKeyValuePair[IString, object]) -> str:
                columns.Push(self.FormatTableName(item.GetKey().ToString()))
                args.Push(item.GetValue())

                return '?'
            
            result: str = join(Select(self.GetItems().AsIterable(), addValue)) # Needs to be executed before values.AsGenerator().

            return DualResult[str, str](join(columns.AsGenerator()), result)
        
        result: DualResult[str, str] = getValues()
        
        return DualResult[str, ICountableEnumerable[object]|None](f"{self._GetStatement(self.IgnoreExisting())} {self.GetFormattedTableName()} ({result.GetKey()}) VALUES ({result.GetValue()})", CreateCountableEnumerable(args))
class MultiInsertionQuery(InsertionQueryBase[Iterable[Iterable[object]]], IMultiInsertionQuery):
    def __init__(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> None:
        super().__init__(tableName, items, ignoreExisting)

        self.__columns: ICountableEnumerable[IString] = columns
    
    @final
    def GetColumns(self) -> ICountableEnumerable[IString]: return self.__columns
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        def join(values: Iterable[str]) -> str: return ", ".join(values)
        
        globalArgs: ICountableEnumerableList[object] = CountableEnumerableQueue[object]()
        columns: ICountableEnumerable[IString] = self.GetColumns()

        def getArguments(values: Iterable[object]) -> str:
            def getResult() -> str|None:
                args: CountableQueue[object]

                def getArgument(value: object) -> str:
                    args.Push(value)

                    return '?'

                args = CountableQueue[object]()
                result: str = join(getArgument(value) for value in values)

                if args.GetCount() == columns.GetCount():
                    globalArgs.PushItems(args.AsGenerator())

                    return f"({result})"
                
                return None
            
            result: str|None = getResult()

            if result is None: raise ValueError("Argument length mismatch.")
            
            return result
        
        return DualResult[str, ICountableEnumerable[object]|None](f"{self._GetStatement(self.IgnoreExisting())} {self.GetFormattedTableName()} ({join(Select(columns.AsIterable(), lambda column: self.FormatTableName(column.ToString())))}) VALUES {join(Select(self.GetItems(), getArguments))}", CreateCountableEnumerable(globalArgs))

class UpdateQuery(WriteQuery, IUpdateQuery):
    def __init__(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet|None) -> None:
        super().__init__(tableName)

        self.__values: IDictionary[IString, object] = values
        self.__conditions: IConditionParameterSet|None = conditions
    
    @final
    def GetValues(self) -> IDictionary[IString, object]: return self.__values
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None: return self.__conditions
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        def addValue(queryBuilder: IConditionalQueryBuilder, item: IKeyValuePair[IString, object]) -> str:
            queryBuilder.GetParameter(item.GetValue())

            return self.FormatTableName(item.GetKey().ToString()) + " = ?"
        
        with (queryBuilder := ConditionalQueryBuilder(self)):
            queryBuilder.OpenStream()

            queryBuilder.Write(f"UPDATE {self.GetFormattedTableName()} SET {Select(self.GetValues().AsIterable(), lambda item: addValue(queryBuilder, item))}")
            
            queryBuilder.AddConditions(self.GetConditions())
            
            return queryBuilder.Build()
        
        raise MemoryError()