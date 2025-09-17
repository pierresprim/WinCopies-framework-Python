from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator, Sequence
from typing import final



from WinCopies import IDisposable, IInterface

from WinCopies.Collections import Enumeration
from WinCopies.Collections.Abstraction import CountableIterable
from WinCopies.Collections.Enumeration import IEnumerator, IIterable, ICountableIterable
from WinCopies.Collections.Enumeration.Extensions import RecursivelyIterable
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Linked import Singly
from WinCopies.Collections.Linked.Singly import Queue, CountableQueue, CountableIterableQueue

from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult



from WinCopies.Data import IColumn
from WinCopies.Data.Misc import IQueryBase
from WinCopies.Data.Parameter import IParameter
from WinCopies.Data.QueryBuilder import ISelectionQueryBuilder, SelectionQueryBuilder, GetPrefixedSelectionQueryWriter
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet, IBranchSet, IJoin

type QueryResult = DualResult[str, ICountableIterable[object]|None]

class IQueryExecutionResult(IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetRowCount(self) -> int:
        pass

class ISelectionQueryExecutionResult(IIterable[Sequence[object]], IQueryExecutionResult):
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

class ISelectionQueryBase(IInterface):
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
    def GetSubqueries(self) -> IIterable[ISubselectionQuery]|None:
        pass
    @abstractmethod
    def SetSubqueries(self, subqueries: IIterable[ISubselectionQuery]|None) -> None:
        pass

class ISelectionQuery(ISelectionQueryBase, INullableQuery[ISelectionQueryExecutionResult]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> IColumnParameterSet[IParameter[object]]:
        pass

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        pass
    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        pass

    @abstractmethod
    def GetCases(self) -> IBranchSet[object]|None:
        pass
    @abstractmethod
    def SetCases(self, cases: IBranchSet[object]|None) -> None:
        pass
class ISubselectionQuery(ISelectionQueryBase):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IKeyValuePair[IColumn, IParameter[object]]:
        pass

class IInsertionQueryBase[T](IQuery[QueryResult, IInsertionQueryExecutionResult]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        pass
    
    @abstractmethod
    def GetItems(self) -> T:
        pass

class IInsertionQuery(IInsertionQueryBase[IDictionary[str, object]]):
    def __init__(self):
        super().__init__()
class IMultiInsertionQuery(IInsertionQueryBase[Iterable[Iterable[object]]]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumns(self) -> Sequence[str]:
        pass

class SelectionQueryBase(ISelectionQueryBase):
    def __init__(self, tables: ITableParameterSet, conditions: IConditionParameterSet|None, subqueries: IIterable[ISubselectionQuery]|None = None):
        super().__init__()
    
        self.__tables: ITableParameterSet = tables
        self.__conditions: IConditionParameterSet|None = conditions
        self.__subqueries: IIterable[ISubselectionQuery]|None = subqueries
    
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
    def GetSubqueries(self) -> IIterable[ISubselectionQuery]|None:
        return self.__subqueries
    @final
    def SetSubqueries(self, subqueries: IIterable[ISubselectionQuery]|None) -> None:
        self.__subqueries = subqueries
class SelectionQuery(SelectionQueryBase, NullableQuery[ISelectionQueryExecutionResult], ISelectionQuery):
    @final
    class __Enumerable(RecursivelyIterable[ISubselectionQuery]):
        @final
        class __IterableSelectionQuery(IIterable[ISubselectionQuery]):
            def __init__(self, query: ISubselectionQuery):
                super().__init__()

                self.__query: ISubselectionQuery = query
            
            def TryGetIterator(self) -> Iterator[ISubselectionQuery]|None:
                queries: Iterable[ISubselectionQuery]|None = self.__query.GetSubqueries()

                return None if queries is None else (query for query in queries)
        
        @final
        class __Enumerator(RecursivelyIterable[ISubselectionQuery].StackedEnumerator):
            def __init__(self, iterable: RecursivelyIterable[ISubselectionQuery], enumerator: IEnumerator[ISubselectionQuery], queryBuilder: ISelectionQueryBuilder):
                super().__init__(iterable, Enumeration.AsEnumerator(enumerator))

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
        
        def __init__(self, queries: IIterable[ISubselectionQuery], queryBuilder: ISelectionQueryBuilder):
            super().__init__()

            self.__queries: IIterable[ISubselectionQuery] = queries
            self.__queryBuilder: ISelectionQueryBuilder = queryBuilder
        
        def _AsRecursivelyIterable(self, container: ISubselectionQuery) -> IIterable[ISubselectionQuery]:
            return SelectionQuery.__Enumerable.__IterableSelectionQuery(container)
        
        def _TryGetRecursiveIterator(self, iterator: IEnumerator[ISubselectionQuery]) -> Iterator[ISubselectionQuery]|None:
            return SelectionQuery.__Enumerable.__Enumerator(self, iterator, self.__queryBuilder)
        
        def TryGetIterator(self) -> Iterator[ISubselectionQuery]|None:
            return self.__queries.TryGetIterator()
    
    def __init__(self, tables: ITableParameterSet, columns: IColumnParameterSet[IParameter[object]], conditions: IConditionParameterSet|None):
        super().__init__(tables, conditions)

        self.__cases: IBranchSet[object]|None = None
        self.__joins: Iterable[IJoin]|None = None
        self.__columns: IColumnParameterSet[IParameter[object]] = columns
    
    @final
    def GetColumns(self) -> IColumnParameterSet[IParameter[object]]:
        return self.__columns

    @final
    def GetJoins(self) -> Iterable[IJoin]|None:
        return self.__joins
    @final
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        self.__joins = joins
    
    @final
    def GetCases(self) -> IBranchSet[object]|None:
        return self.__cases
    @final
    def SetCases(self, cases: IBranchSet[object]|None) -> None:
        self.__cases = cases
    
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
            
            return queryBuilder.Join(queryBuilder.AddTable(table.GetKey(), table.GetValue()) for table in query.GetTables())
        
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
                subqueries: Iterable[ISubselectionQuery]|None = self.GetSubqueries()

                if subqueries is None:
                    return False # No subquery; continue query building.
                
                for query in SelectionQuery.__Enumerable(subqueries, queryBuilder):
                    if not self._PrevalidateQuery(query):
                        return True # A subquery failed to validate; cancel query building.
                    
                    queryBuilder.Write(f"SELECT {queryBuilder.ProcessCondition(query.GetColumn())} FROM {getTables(query)}")
                
                return False # Process succeeded; continue query building.
            
            def addCases() -> None:
                cases: IBranchSet[object]|None = self.GetCases()

                if cases is None:
                    return
                
                cases.Render(GetPrefixedSelectionQueryWriter(', ', queryBuilder))
            
            queryBuilder.Write(f"SELECT {getColumns()}")

            addCases()

            if getSubqueries():
                return True # Cancel query building.
            
            queryBuilder.Write(f" FROM {getTables(self)}")

            queryBuilder.AddJoins(self.GetJoins())

            return False # Continue query rendering.
        
        with (queryBuilder := SelectionQueryBuilder(self)):
            queryBuilder.OpenStream()

            if initQuery():
                return None
            
            queryBuilder.AddConditions(self.GetConditions())
            
            return queryBuilder.Build()
class SubselectionQuery(SelectionQueryBase, ISubselectionQuery):
    def __init__(self, tables: ITableParameterSet, column: IKeyValuePair[IColumn, IParameter[object]], conditions: IConditionParameterSet|None, subqueries: IIterable[ISubselectionQuery]|None = None):
        super().__init__(tables, conditions, subqueries)

        self.__column: IKeyValuePair[IColumn, IParameter[object]] = column
    
    @final
    def GetColumn(self) -> IKeyValuePair[IColumn, IParameter[object]]:
        return self.__column

class InsertionQueryBase[T](Query[IInsertionQueryExecutionResult], IInsertionQueryBase[T]):
    def __init__(self, tableName: str, items: T):
        super().__init__()

        self.__tableName: str = tableName
        self.__items: T = items
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    @final
    def GetFormattedTableName(self) -> str:
        return self.FormatTableName(self.GetTableName())
    
    @final
    def GetItems(self) -> T:
        return self.__items

class InsertionQuery(InsertionQueryBase[IDictionary[str, object]], IInsertionQuery):
    def __init__(self, tableName: str, items: IDictionary[str, object]):
        super().__init__(tableName, items)
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        args: CountableIterableQueue[object] = CountableIterableQueue[object]()

        def getValues() -> DualResult[str, str]:
            def join(values: Iterable[str]) -> str:
                return ", ".join(values)

            values: Singly.IList[str] = Queue[str]()

            def addValue(item: IKeyValuePair[str, object]) -> str:
                values.Push(item.GetKey())
                args.Push(item.GetValue())

                return str('?')
            
            result: str = join(addValue(item) for item in self.GetItems())

            return DualResult[str, str](join(values.AsGenerator()), result)
        
        result: DualResult[str, str] = getValues()
        
        return DualResult[str, ICountableIterable[object]](f"INSERT INTO {self.GetFormattedTableName()} ({result.GetKey()}) VALUES ({result.GetValue()})", CountableIterable[object].Create(args))
class MultiInsertionQuery(InsertionQueryBase[Iterable[Iterable[object]]], IMultiInsertionQuery):
    def __init__(self, tableName: str, items: Iterable[Iterable[object]], *columns: str):
        super().__init__(tableName, items)

        self.__columns: Sequence[str] = columns
    
    @final
    def GetColumns(self) -> Sequence[str]:
        return self.__columns
    
    @final
    def _GetQueryOverride(self) -> QueryResult:
        def join(values: Iterable[str]) -> str:
            return ", ".join(values)
        
        globalArgs: CountableIterableQueue[object] = CountableIterableQueue[object]()
        columns: Sequence[str] = self.GetColumns()

        length: int = len(columns)

        def getArguments(values: Iterable[object]) -> str:
            def getResult() -> str|None:
                def getResult(args: CountableQueue[object]) -> str|None:
                    def getArguments(value: object) -> str:
                        args.Push(value)

                        return '?'

                    result: str|None = join(getArguments(value) for value in values)

                    if args.GetCount() == length:
                        globalArgs.PushItems(args.AsGenerator())

                        result = f"({result})"
                    
                    else:
                        result = None

                    return result

                args: CountableQueue[object]|None = CountableQueue[object]()
                
                return getResult(args)
            
            result: str|None = getResult()

            if result is None:
                raise ValueError("Argument length mismatch.")
            
            return result
        
        return DualResult[str, ICountableIterable[object]](f"INSERT INTO {self.GetFormattedTableName()} ({join(columns)}) VALUES {join(getArguments(item) for item in self.GetItems())}", CountableIterable[object].Create(globalArgs))