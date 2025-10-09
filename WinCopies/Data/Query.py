from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import final



from WinCopies import IDisposable, IInterface

from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Abstraction.Enumeration import CountableEnumerable
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable, IEnumerator, Enumerable, TryGetEnumerator
from WinCopies.Collections.Enumeration.Extensions import RecursivelyEnumerable
from WinCopies.Collections.Extensions import ICollection, IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Linked import Singly
from WinCopies.Collections.Linked.Singly import ICountableEnumerableList, Queue, CountableQueue, CountableEnumerableQueue

from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Object import IValueItem, IString
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult



from WinCopies.Data import IColumn
from WinCopies.Data.Misc import IQueryBase
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.QueryBuilder import IConditionalQueryBuilder, ISelectionQueryBuilder, ConditionalQueryBuilder, SelectionQueryBuilder, GetPrefixedSelectionQueryWriter
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet, IBranchSet, IJoin

type QueryResult = DualResult[str, ICountableEnumerable[object]|None]

class IQueryExecutionResult(IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetRowCount(self) -> int:
        pass

class ISelectionQueryExecutionResult(IEnumerable[Sequence[object]], IQueryExecutionResult):
    def __init__(self):
        super().__init__()
class IInsertionQueryExecutionResult(IQueryExecutionResult):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetLastRowId(self) -> int:
        pass

class IQuery[TQueryResult, TQueryExecutionResult: IQueryExecutionResult|None](IQueryBase[TQueryResult]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def Execute(self) -> TQueryExecutionResult:
        pass

class QueryProvider[T](IQueryBase[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _Validate(self) -> str|None:
        pass
class QueryBase[TQueryResult, TQueryExecutionResult: IQueryExecutionResult|None](QueryProvider[TQueryResult], IQuery[TQueryResult, TQueryExecutionResult]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetQueryOverride(self) -> TQueryResult:
        pass

    def GetQuery(self) -> TQueryResult:
        result: str|None = self._Validate()
        
        if result is None:
            return self._GetQueryOverride()
        
        raise InvalidOperationError(result)
class Query[T: IQueryExecutionResult](QueryBase[QueryResult, T]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetQuery(self) -> QueryResult:
        return super().GetQuery()

class INullableQueryBase(IQueryBase[QueryResult|None]):
    def __init__(self):
        super().__init__()
class INullableQuery[T: IQueryExecutionResult](INullableQueryBase, IQuery[QueryResult|None, T|None]):
    def __init__(self):
        super().__init__()

class NullableQueryProvider(QueryProvider[QueryResult|None]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _Prevalidate(self) -> bool:
        pass
class NullableQuery[T: IQueryExecutionResult](NullableQueryProvider, QueryBase[QueryResult|None, T|None], INullableQuery[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def GetQuery(self) -> QueryResult|None:
        return super().GetQuery() if self._Prevalidate() else None

class IConditionalQuery(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        pass
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass

class ISelectionQueryBase(IConditionalQuery):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTables(self) -> ITableParameterSet:
        pass
    
    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        pass
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass

    @abstractmethod
    def GetSubqueries(self) -> IEnumerable[ISubselectionQuery]|None:
        pass
    @abstractmethod
    def SetSubqueries(self, subqueries: IEnumerable[ISubselectionQuery]|None) -> None:
        pass

class ISelectionQuery(ISelectionQueryBase, INullableQuery[ISelectionQueryExecutionResult]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> IColumnParameterSet[IParameter[object]]:
        pass

    @abstractmethod
    def GetJoins(self) -> ICollection[IJoin]:
        pass
    @abstractmethod
    def GetCases(self) -> ICollection[IBranchSet[IValueItem]]:
        pass
class ISubselectionQuery(ISelectionQueryBase):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IKeyValuePair[IColumn, IParameter[object]]:
        pass

class IWriteQuery(IQuery[QueryResult, IInsertionQueryExecutionResult]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        pass

class IInsertionQueryBase[T](IWriteQuery):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetItems(self) -> T:
        pass

class IInsertionQuery(IInsertionQueryBase[IDictionary[IString, object]]):
    def __init__(self):
        super().__init__()
class IMultiInsertionQuery(IInsertionQueryBase[Iterable[Iterable[object]]]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> ICountableEnumerable[IString]:
        pass

class IUpdateQuery(IWriteQuery, IConditionalQuery):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValues(self) -> IDictionary[IString, object]:
        pass

class SelectionQueryBase(ISelectionQueryBase):
    def __init__(self, tables: ITableParameterSet, conditions: IConditionParameterSet|None, subqueries: IEnumerable[ISubselectionQuery]|None = None):
        super().__init__()
    
        self.__tables: ITableParameterSet = tables
        self.__conditions: IConditionParameterSet|None = conditions
        self.__subqueries: IEnumerable[ISubselectionQuery]|None = subqueries
    
    @final
    def _PrevalidateQuery(self, query: ISelectionQueryBase) -> bool:
        return query.GetTables().GetCount() > 0
    @final
    def _Prevalidate(self) -> bool:
        return self._PrevalidateQuery(self)
    
    @final
    def GetTables(self) -> ITableParameterSet:
        return self.__tables
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        self.__conditions = conditions
    
    @final
    def GetSubqueries(self) -> IEnumerable[ISubselectionQuery]|None:
        return self.__subqueries
    @final
    def SetSubqueries(self, subqueries: IEnumerable[ISubselectionQuery]|None) -> None:
        self.__subqueries = subqueries
class SelectionQuery(SelectionQueryBase, NullableQuery[ISelectionQueryExecutionResult], ISelectionQuery):
    @final
    class __Enumerable(RecursivelyEnumerable[ISubselectionQuery]):
        @final
        class __IterableSelectionQuery(Enumerable[ISubselectionQuery]):
            def __init__(self, query: ISubselectionQuery):
                super().__init__()

                self.__query: ISubselectionQuery = query
            
            def TryGetEnumerator(self) -> IEnumerator[ISubselectionQuery]|None:
                return TryGetEnumerator(self.__query.GetSubqueries())
        
        @final
        class __Enumerator(RecursivelyEnumerable[ISubselectionQuery].StackedEnumerator):
            def __init__(self, enumerable: RecursivelyEnumerable[ISubselectionQuery], enumerator: IEnumerator[ISubselectionQuery], queryBuilder: ISelectionQueryBuilder):
                super().__init__(enumerable, enumerator)

                self.__queryBuilder: ISelectionQueryBuilder = queryBuilder
            
            def __Write(self, value: str) -> None:
                self.__queryBuilder.Write(value)
            
            def _OnEnteringMainLevel(self, item: ISubselectionQuery, enumerator: IEnumerator[ISubselectionQuery]):
                self.__Write(', ')
                
                return True
            
            def _OnEnteringLevel(self, item: ISubselectionQuery, enumerator: IEnumerator[ISubselectionQuery]) -> None:
                self.__Write('(')
            
            def _OnExitingLevel(self, cookie: ISubselectionQuery) -> None:
                self.__queryBuilder.AddConditions(cookie.GetConditions())
                self.__Write(')')
        
        def __init__(self, queries: IEnumerable[ISubselectionQuery], queryBuilder: ISelectionQueryBuilder):
            super().__init__()

            self.__queries: IEnumerable[ISubselectionQuery] = queries
            self.__queryBuilder: ISelectionQueryBuilder = queryBuilder
        
        def _AsRecursivelyEnumerable(self, container: ISubselectionQuery) -> IEnumerable[ISubselectionQuery]:
            return SelectionQuery.__Enumerable.__IterableSelectionQuery(container)
        
        def _TryGetRecursiveEnumerator(self, enumerator: IEnumerator[ISubselectionQuery]) -> IEnumerator[ISubselectionQuery]|None:
            return SelectionQuery.__Enumerable.__Enumerator(self, enumerator, self.__queryBuilder)
        
        def TryGetEnumerator(self) -> IEnumerator[ISubselectionQuery]|None:
            return self.__queries.TryGetEnumerator()
    
    def __init__(self, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None):
        super().__init__(tables, conditions)

        self.__cases: ICollection[IBranchSet[IValueItem]] = List[IBranchSet[IValueItem]]()
        self.__joins: ICollection[IJoin] = List[IJoin]()
        self.__columns: IColumnParameterSet[IParameter[object]] = columns
    
    @final
    def GetColumns(self) -> IColumnParameterSet[IParameter[object]]:
        return self.__columns

    @final
    def GetJoins(self) -> ICollection[IJoin]:
        return self.__joins
    @final
    def GetCases(self) -> ICollection[IBranchSet[IValueItem]]:
        return self.__cases
    
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
            def getColumns() -> str:
                return queryBuilder.Join(queryBuilder.ProcessConditions(self.GetColumns()))
            
            def getSubqueries() -> bool:
                """
                Parses the subqueries of the current main query and adds the result to the memory stream and the arguments to the query argument list.

                Returns:
                A boolean value indicating whether the query building initialization FAILED (for optimization reason).
                """
                subqueries: IEnumerable[ISubselectionQuery]|None = self.GetSubqueries()

                if subqueries is None:
                    return False # No subquery; continue query building.
                
                for query in SelectionQuery.__Enumerable(subqueries, queryBuilder).AsIterable():
                    if not self._PrevalidateQuery(query):
                        return True # A subquery failed to validate; cancel query building.
                    
                    queryBuilder.Write(f"SELECT {queryBuilder.ProcessCondition(query.GetColumn())} FROM {getTables(query)}")
                
                return False # Process succeeded; continue query building.
            
            def addCases() -> None:
                for case in self.GetCases().AsIterable():
                    case.Render(GetPrefixedSelectionQueryWriter(', ', queryBuilder))
            
            queryBuilder.Write(f"SELECT {getColumns()}")

            addCases()

            if getSubqueries():
                return True # Cancel query building.
            
            queryBuilder.Write(f" FROM {getTables(self)}")

            queryBuilder.AddJoins(self.GetJoins().AsIterable())

            return False # Continue query rendering.
        
        with (queryBuilder := SelectionQueryBuilder(self)):
            queryBuilder.OpenStream()

            if initQuery():
                return None
            
            queryBuilder.AddConditions(self.GetConditions())
            
            return queryBuilder.Build()
        
        raise MemoryError()
class SubselectionQuery(SelectionQueryBase, ISubselectionQuery):
    def __init__(self, tables: ITableParameterSet, column: IKeyValuePair[IColumn, IParameter[object]], conditions: IConditionParameterSet|None, subqueries: IEnumerable[ISubselectionQuery]|None = None):
        super().__init__(tables, conditions, subqueries)

        self.__column: IKeyValuePair[IColumn, IParameter[object]] = column
    
    @final
    def GetColumn(self) -> IKeyValuePair[IColumn, IParameter[object]]:
        return self.__column

class WriteQuery(Query[IInsertionQueryExecutionResult], IWriteQuery):
    def __init__(self, tableName: str):
        super().__init__()

        self.__tableName: str = tableName
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    @final
    def GetFormattedTableName(self) -> str:
        return self.FormatTableName(self.GetTableName())

class InsertionQueryStatementProvider(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetStatement(self, ignoreExisting: bool = False) -> str:
        pass
class InsertionQueryBase[T](WriteQuery, IInsertionQueryBase[T], InsertionQueryStatementProvider):
    def __init__(self, tableName: str, items: T, ignoreExisting: bool = False):
        super().__init__(tableName)

        self.__items: T = items
        self.__ignoreExisting: bool = ignoreExisting
    
    @final
    def GetItems(self) -> T:
        return self.__items
    
    @final
    def GetIgnoreExisting(self) -> bool:
        return self.__ignoreExisting

class InsertionQuery(InsertionQueryBase[IDictionary[IString, object]], IInsertionQuery):
    def __init__(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False):
        super().__init__(tableName, items, ignoreExisting)
    
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
            def join(values: Iterable[str]) -> str:
                return ", ".join(values)

            columns: Singly.IList[str] = Queue[str]()

            def addValue(item: IKeyValuePair[IString, object]) -> str:
                columns.Push(self.FormatTableName(item.GetKey().ToString()))
                args.Push(item.GetValue())

                return '?'
            
            result: str = join(Select(self.GetItems().AsIterable(), addValue)) # Needs to be executed before values.AsGenerator().

            return DualResult[str, str](join(columns.AsGenerator()), result)
        
        result: DualResult[str, str] = getValues()
        
        return DualResult[str, ICountableEnumerable[object]](f"{self._GetStatement(self.GetIgnoreExisting())} {self.GetFormattedTableName()} ({result.GetKey()}) VALUES ({result.GetValue()})", CountableEnumerable[object].Create(args))
class MultiInsertionQuery(InsertionQueryBase[Iterable[Iterable[object]]], IMultiInsertionQuery):
    def __init__(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False):
        super().__init__(tableName, items, ignoreExisting)

        self.__columns: ICountableEnumerable[IString] = columns
    
    @final
    def GetColumns(self) -> ICountableEnumerable[IString]:
        return self.__columns
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        def join(values: Iterable[str]) -> str:
            return ", ".join(values)
        
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

            if result is None:
                raise ValueError("Argument length mismatch.")
            
            return result
        
        return DualResult[str, ICountableEnumerable[object]](f"{self._GetStatement(self.GetIgnoreExisting())} {self.GetFormattedTableName()} ({join(Select(columns.AsIterable(), lambda column: self.FormatTableName(column.ToString())))}) VALUES {join(Select(self.GetItems(), getArguments))}", CountableEnumerable[object].Create(globalArgs))

class UpdateQuery(WriteQuery, IUpdateQuery):
    def __init__(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet|None):
        super().__init__(tableName)

        self.__values: IDictionary[IString, object] = values
        self.__conditions: IConditionParameterSet|None = conditions
    
    @final
    def GetValues(self) -> IDictionary[IString, object]:
        return self.__values
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    
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