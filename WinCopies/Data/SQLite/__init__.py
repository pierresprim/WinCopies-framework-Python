from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import auto, Enum, Flag
from typing import final

import sqlite3



from WinCopies import IDisposable, String

from WinCopies.Collections import Generator, MakeIterable
from WinCopies.Collections.Abstraction import Array
from WinCopies.Collections.Extensions import IArray, IDictionary
from WinCopies.Collections.Iteration import EnsureOnlyOne

from WinCopies.Enum import HasFlag

from WinCopies.Typing import InvalidOperationError, GetDisposedError
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Typing.Reflection import EnsureDirectModuleCall



from WinCopies.Data import Abstract, Column, TableColumn, Operator
from WinCopies.Data.Abstract import ITable
from WinCopies.Data.Extensions import GetField
from WinCopies.Data.Factory import IFieldFactory, IQueryFactory
from WinCopies.Data.Field import FieldType, FieldAttributes, IntegerMode, RealMode, TextMode, IField
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IParameter, FieldParameter, ColumnParameter, TableParameter, MakeTableColumnIterable, MakeTableValueIterable, GetNullFieldParameter
from WinCopies.Data.Query import ISelectionQuery, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet
from WinCopies.Data.Set.Extensions import Join, ColumnParameterSet, FieldParameterSet, ConditionParameterSet, TableParameterSet, ExistenceSet, IExistenceQuery, ExistenceQuery, MakeFieldParameterSetIterable

from WinCopies.Data.SQLite.Factory import FieldFactory, QueryFactory

@final
class Table(Abstract.Table):
    @final
    class __Connection(IDisposable):
        def __init__(self, connection: Connection) -> None:
            self.__connection: Connection|None = connection
        
        def GetConnection(self) -> Connection:
            if self.__connection is None:
                raise InvalidOperationError()
            
            return self.__connection
        
        def Dispose(self) -> None:
            self.__connection = None
    
    class FieldAttributes(Flag):
        Null = 0
        Integer = auto()
        PrimaryKey = auto()
        NoDefault = auto()
        Unique = auto()
        Nullable = auto()
    
    def __init__(self, connection: Connection, name: str):
        EnsureDirectModuleCall()
        
        super().__init__()
        
        self.__connection: Table.__Connection = Table.__Connection(connection)
        self.__name: str = name
        self.__fields: IArray[IField]|None = None
    
    def __GetConnection(self) -> Connection:
        return self.__connection.GetConnection()
    
    def GetName(self) -> str:
        return self.__name
    
    def GetFields(self) -> IArray[IField]:
        if self.__fields is None:
            def getFields(connection: Connection) -> Generator[IField]:
                def getFieldType(fieldType: str) -> DualResult[FieldType, Enum|None]:
                    def getResult(fieldType: FieldType, fieldMode: Enum|None) -> DualResult[FieldType, Enum|None]:
                        return DualResult[FieldType, Enum|None](fieldType, fieldMode)
                    
                    match fieldType.upper():
                        case "INTEGER" | "INT":
                            return getResult(FieldType.Integer, IntegerMode.Long)
                        
                        case "REAL" | "FLOAT" | "DOUBLE":
                            return getResult(FieldType.Real, RealMode.Double)
                        
                        case "TEXT" | "VAR" | "VARCHAR":
                            return getResult(FieldType.Text, TextMode.Text)
                        
                        case '':
                            return getResult(FieldType.Null, None)
                        
                        case _:
                            raise NotImplementedError(f"The '{fieldType}' field type is not supported.")
                
                def getAttribute(attributes: Table.FieldAttributes) -> FieldAttributes:
                    if attributes == Table.FieldAttributes.Null:
                        return FieldAttributes.Null
                    
                    def check(value: Table.FieldAttributes) -> bool:
                        return HasFlag(attributes, value)
                    
                    result: FieldAttributes = FieldAttributes.Null
                    
                    if check(Table.FieldAttributes.PrimaryKey):
                        result = FieldAttributes.PrimaryKey
                        
                        if check(Table.FieldAttributes.Integer) and check(Table.FieldAttributes.NoDefault):
                            result |= FieldAttributes.AutoIncrement
                    
                    if check(Table.FieldAttributes.Unique):
                        result |= FieldAttributes.Unique
                    
                    if check(Table.FieldAttributes.Nullable):
                        result |= FieldAttributes.Nullable
                    
                    return result
                
                def checkAttributeValue(row: Sequence[object], index: int) -> bool:
                    return int(row[index]) > 0 # type: ignore
                
                result: DualResult[FieldType, Enum|None]|None = None
                query: ISelectionQuery = connection.GetQueryFactory().GetSelectionQuery(
                    TableParameterSet(
                        {"PRAGMA_TABLE_INFO": TableParameter(
                            't', MakeTableValueIterable(self.GetName()))}),
                    ColumnParameterSet[IParameter[object]](
                        {Column("name"): None,
                         Column("type"): None,
                         Column("pk"): None,
                         Column("dflt_value"): GetNullFieldParameter(),
                         Column("notnull"): FieldParameter[int].Create(Operator.LessThanOrEquals, 0)}))
                
                uniqueFlagQuery: IExistenceQuery = ExistenceQuery(
                    "PRAGMA_INDEX_LIST",
                    TableParameter[object](
                        'i',
                        MakeTableValueIterable(self.GetName())),
                    ConditionParameterSet(
                        MakeFieldParameterSetIterable(
                            {TableColumn('i', "unique"): FieldParameter[int].Create(Operator.Equals, 1)})))
                uniqueFlagQuery.SetJoins(
                    MakeIterable(
                        Join(
                            JoinType.Inner,
                            "PRAGMA_INDEX_INFO",
                            TableParameter(
                                "info",
                                MakeTableColumnIterable(
                                    TableColumn('i', "name"))),
                            ConditionParameterSet(
                                MakeFieldParameterSetIterable(
                                    {TableColumn("info", "cid"): ColumnParameter.CreateForTableColumn(Operator.Equals, 't', "cid")})))))

                query.SetCases(ExistenceSet("isUnique", uniqueFlagQuery))

                columns: ISelectionQueryExecutionResult|None = query.Execute()

                if columns is None:
                    return
                
                fieldFactory: IFieldFactory = connection.GetFieldFactory()
                attributes: Table.FieldAttributes|None = None

                for row in columns:
                    result = getFieldType(str(row[1]))

                    attributes = Table.FieldAttributes.Null

                    if result.GetKey() == FieldType.Integer:
                        attributes |= Table.FieldAttributes.Integer
                    if checkAttributeValue(row, 2):
                        attributes |= Table.FieldAttributes.PrimaryKey
                    if checkAttributeValue(row, 3):
                        attributes |= Table.FieldAttributes.NoDefault
                    if checkAttributeValue(row, 4):
                        attributes |= Table.FieldAttributes.Nullable
                    if checkAttributeValue(row, 5):
                        attributes |= Table.FieldAttributes.Unique

                    yield GetField(fieldFactory, str(row[0]), getAttribute(attributes), result.GetKey(), result.GetValue())
            
            self.__fields = Array[IField](getFields(self.__GetConnection()))
        
        return self.__fields
    
    def Select(self, columns: IColumnParameterSet[IParameter[object]]) -> ISelectionQueryExecutionResult|None:
        return self.__GetConnection().GetQueryFactory().GetSelectionQuery(TableParameterSet.Create(self.GetName()), columns).Execute()
    
    def Insert(self, items: IDictionary[str, object]) -> IInsertionQueryExecutionResult:
        return self.__GetConnection().GetQueryFactory().GetInsertionQuery(self.GetName(), items).Execute()
    def InsertMultiple(self, items: Iterable[Iterable[object]], *columns: str) -> IInsertionQueryExecutionResult:
        return self.__GetConnection().GetQueryFactory().GetMultiInsertionQuery(self.GetName(), items, *columns).Execute()
    
    def Dispose(self) -> None:
        self.__fields = None
        self.__connection.Dispose()

@final
class Connection(Abstract.Connection):
    def __DoCreateTable(self, connection: sqlite3.Connection, query: str, name: str, fields: Iterable[IField]) -> None:
        connection.execute(f"CREATE TABLE {query}{self.FormatTableName(name)} ({", ".join(field.ToString() for field in fields)}) STRICT")
    def __TryCreateTable(self, name: str, fields: Iterable[IField]) -> None:
        if self.__connection is None:
            raise GetDisposedError()
        
        self.__DoCreateTable(self.__connection, "IF NOT EXISTS ", name, fields)

        return None
    def __CreateTable(self, name: str, fields: Iterable[IField]) -> ITable:
        if self.__connection is None:
            raise GetDisposedError()
        
        self.__DoCreateTable(self.__connection, '', name, fields)

        return Table(self, name)
    
    def __init__(self, path: str):
        super().__init__()

        self.__path: str = path
        self.__connection: sqlite3.Connection|None = None
    
    def Open(self) -> bool:
        self.__connection = sqlite3.connect(self.__path, autocommit = False)

        return True
    
    def FormatTableName(self, name: str) -> str:
        return String.DoubleQuoteSurround(name)
    
    def GetTableNames(self) -> Generator[str]:
        queryExecutionResult: ISelectionQueryExecutionResult|None = self.GetQueryFactory().GetSelectionQuery(TableParameterSet.Create("sqlite_master"), ColumnParameterSet({Column("name"): None}), ConditionParameterSet(MakeIterable(FieldParameterSet({Column("type"): FieldParameter[str].Create(Operator.Equals, "table")})))).Execute()

        if queryExecutionResult is None:
            return

        for row in queryExecutionResult:
            yield str(row[0])
    
    @staticmethod
    def __EnsureFields(fields: Iterable[IField]) -> None:
        EnsureOnlyOne(fields, lambda field: field.GetAttribute() == FieldAttributes.AutoIncrement, f"The '{FieldAttributes.AutoIncrement.name}' must be set to at most one field.")
    
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField]) -> ITable|None:
        Connection.__EnsureFields(fields)

        self.__TryCreateTable(name, fields)
    def _CreateTableOverride(self, name: str, fields: Iterable[IField]) -> ITable:
        Connection.__EnsureFields(fields)
        
        return self.__CreateTable(name, fields)

    def _GetTable(self, name: str) -> ITable:
        return Table(self, name)
    
    def _GetFieldFactory(self) -> IFieldFactory:
        return FieldFactory()
    def _GetQueryFactory(self) -> IQueryFactory:
        if self.__connection is None:
            raise GetDisposedError()
        
        return QueryFactory(self.__connection)
    
    def Commit(self) -> bool:
        if self.__connection is None:
            return False
        
        self.__connection.commit()

        return True

    def _CloseOverride(self) -> None:
        if self.__connection is None:
            return
        
        self.__connection.close()
        self.__connection = None