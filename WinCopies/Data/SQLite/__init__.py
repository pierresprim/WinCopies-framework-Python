from __future__ import annotations

from collections.abc import Iterable, Sequence
from enum import auto, Enum, Flag
from typing import final, Callable

import sqlite3



from WinCopies import IInterface, IDisposable

from WinCopies.Collections import Generator, MakeSequence
from WinCopies.Collections.Abstraction.Collection import Array, Dictionary
from WinCopies.Collections.Extensions import IArray
from WinCopies.Collections.Iteration import Append, Select, EnsureOnlyOne
from WinCopies.Collections.Linked import Singly
from WinCopies.Collections.Linked.Singly import Queue

from WinCopies.Enum import HasFlag

from WinCopies.String import DoubleQuoteSurround

from WinCopies.Typing import InvalidOperationError, IEnumValue, EnumValue, String, GetDisposedError
from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Pairing import DualResult
from WinCopies.Typing.Reflection import EnsureDirectModuleCall



from WinCopies.Data import Abstract, IColumn, Column, TableColumn, IOperand, Operator
from WinCopies.Data.Abstract import IConnection, ITable
from WinCopies.Data.Extensions import GetField
from WinCopies.Data.Factory import IFieldFactory, IQueryFactory, IIndexFactory
from WinCopies.Data.Field import FieldType, FieldAttributes, IntegerMode, RealMode, TextMode, IField
from WinCopies.Data.Index import IndexKind, IIndex
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IParameter, FieldParameter, ColumnParameter, TableParameter, MakeTableColumnIterable, MakeTableValueIterable, GetNullFieldParameter, GetNotNullFieldParameter
from WinCopies.Data.Query import ISelectionQuery, ISelectionQueryExecutionResult
from WinCopies.Data.Set.Extensions import Join, ColumnParameterSet, ConditionParameterSet, TableParameterSet, ConditionSet, ExistenceSet, IExistenceQuery, ExistenceQuery, MakeFieldParameterSetEnumerable

from WinCopies.Data.SQLite.Factory import FieldFactory, QueryFactory, IndexFactory

@final
class _Connection(IInterface):
    def __init__(self, connection: Connection, innerCollection: sqlite3.Connection):
        super().__init__()

        self.__connection: IConnection = connection
        self.__innerCollection: sqlite3.Connection = innerCollection
    
    def GetConnection(self) -> IConnection:
        return self.__connection
    
    def GetInnerConnection(self) -> sqlite3.Connection:
        return self.__innerCollection

@final
class Table(Abstract.Table):
    @final
    class __Connection(IDisposable):
        def __init__(self, connection: _Connection) -> None:
            self.__connection: _Connection|None = connection
        
        def GetConnection(self) -> IConnection:
            if self.__connection is None:
                raise InvalidOperationError()
            
            return self.__connection.GetConnection()
        
        def Execute(self, sql: str, values: Sequence[object]|None = None) -> None:
            if self.__connection is None:
                raise InvalidOperationError()
            
            connection: sqlite3.Connection = self.__connection.GetInnerConnection()

            if values is None:
                connection.execute(sql)
            
            else:
                connection.execute(sql, values)
        
        def Dispose(self) -> None:
            self.__connection = None
    
    class FieldAttributes(Flag):
        Null = 0
        Integer = auto()
        PrimaryKey = auto()
        NoDefault = auto()
        Unique = auto()
        Nullable = auto()
    
    def __init__(self, connection: _Connection, name: str):
        EnsureDirectModuleCall()
        
        super().__init__()
        
        self.__connection: Table.__Connection = Table.__Connection(connection)
        self.__name: str = name
        self.__fields: IArray[IField]|None = None
        self.__indices: IArray[IIndex]|None = None
    
    def __GetArray[T](self, converter: Converter[IConnection, Iterable[T]]) -> IArray[T]:
        return Array[T](converter(self._GetConnection()))
    
    def _GetConnection(self) -> IConnection:
        return self.__connection.GetConnection()
    
    def GetName(self) -> str:
        return self.__name
    def SetName(self, name: str) -> None:
        connection: IConnection = self._GetConnection()

        self.__connection.Execute(f"ALTER TABLE {connection.FormatTableName(self.GetName())} RENAME TO {connection.FormatTableName(name)}")
    
    def GetFields(self) -> IArray[IField]:
        def getFields(connection: IConnection) -> Generator[IField]:
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
            
            def getAttributes(attributes: Table.FieldAttributes) -> FieldAttributes:
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
            
            def executeQuery(connection: IConnection) -> ISelectionQueryExecutionResult|None:
                query: ISelectionQuery = connection.GetQueryFactory().GetSelectionQuery(
                    TableParameterSet({
                        String("PRAGMA_TABLE_INFO"): TableParameter[str](
                            't', MakeTableValueIterable(self.GetName()))}),
                    ColumnParameterSet[IParameter[object]]({
                        Column("name"): None,
                        Column("type"): None,
                        Column("pk"): None,
                        Column("dflt_value"): GetNullFieldParameter(),
                        Column("notnull"): FieldParameter[int].Create(Operator.LessThanOrEquals, 0)}))
                
                uniqueFlagQuery: IExistenceQuery = ExistenceQuery(
                    "PRAGMA_INDEX_LIST",
                    TableParameter[str](
                        'i',
                        MakeTableValueIterable(self.GetName())),
                    ConditionParameterSet(
                        MakeFieldParameterSetEnumerable(
                            {TableColumn('i', "unique"): FieldParameter[int].Create(Operator.Equals, 1)})))
                uniqueFlagQuery.SetJoins(
                    MakeSequence(
                        Join(
                            JoinType.Inner,
                            "PRAGMA_INDEX_INFO",
                            TableParameter[IColumn](
                                "info",
                                MakeTableColumnIterable(
                                    TableColumn('i', "name"))),
                            ConditionParameterSet(
                                MakeFieldParameterSetEnumerable({
                                    TableColumn("info", "cid"): ColumnParameter.CreateForTableColumn(Operator.Equals, 't', "cid")})))))

                query.GetCases().Add(ExistenceSet("isUnique", uniqueFlagQuery))

                return query.Execute()

            columns: ISelectionQueryExecutionResult|None = executeQuery(connection)

            if columns is None:
                return
            
            fieldFactory: IFieldFactory = connection.GetFieldFactory()
            attributes: Table.FieldAttributes|None = None
            result: DualResult[FieldType, Enum|None]|None = None

            for row in columns.AsIterable():
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

                yield GetField(fieldFactory, str(row[0]), getAttributes(attributes), result.GetKey(), result.GetValue())
            
        if self.__fields is None:
            self.__fields = self.__GetArray(getFields)
        
        return self.__fields

    @final
    def GetIndices(self) -> IArray[IIndex]:
        def getIndices(connection: IConnection) -> Iterable[IIndex]:
            def getIndices(connection: IConnection) -> Generator[IIndex]:
                def checkIndexKind(factory: IIndexFactory, name: str, kind: IndexKind, columnName: str) -> IIndex|None:
                    return factory.GetNormalIndex(name, columnName) if kind == IndexKind.Normal else None
                
                def getParser() -> Callable[[IIndexFactory, str, str, IndexKind, str, Singly.IList[str]], Generator[IIndex]|None]:
                    return lambda factory, currentName, name, kind, columnName, columns: parse(factory, name, kind, columnName, columns)
                
                def _parse(factory: IIndexFactory, currentName: str, name: str, kind: IndexKind, columnName: str, columns: Singly.IList[str]) -> Generator[IIndex]|None:
                    nonlocal func

                    def push() -> None:
                        columns.Push(columnName)
                    
                    def getIndex() -> IIndex:
                        match kind:
                            case IndexKind.Unique:
                                return factory.GetUnicityIndex(currentName, Select(columns.AsGenerator(), lambda value: String(value)))
                            case IndexKind.PrimaryKey:
                                return factory.GetPrimaryKey(currentName, Select(columns.AsGenerator(), lambda value: String(value)))
                            case _:
                                raise ValueError("The index kind is not valid.")
                    
                    if currentName == name:
                        push()

                        return None
                    
                    index: IIndex|None = checkIndexKind(factory, name, kind, columnName)

                    if index is None:
                        index = getIndex()
                        
                        push()

                        yield index
                    
                    else:
                        yield getIndex()

                        yield index

                        func = getParser()
                
                def parse(factory: IIndexFactory, name: str, kind: IndexKind, columnName: str, columns: Singly.IList[str]) -> Generator[IIndex]|None:
                    # TODO: Use GROUP_CONCAT instead.

                    nonlocal func

                    index: IIndex|None = checkIndexKind(factory, name, kind, columnName)

                    if index is None:
                        columns.Push(columnName)

                        func = _parse

                        return None
                    
                    yield index
                
                def executeQuery(connection: IConnection) -> ISelectionQueryExecutionResult|None:
                    query: ISelectionQuery = connection.GetQueryFactory().GetSelectionQuery(
                        TableParameterSet({
                            String("PRAGMA_INDEX_LIST"): TableParameter(
                                'il', MakeTableValueIterable(self.GetName()))}),
                        ColumnParameterSet[IParameter[object]]({
                            TableColumn("il", "name"): None,
                            TableColumn("ii", "seqno"): None,
                            TableColumn("ii", "name"): None,
                            TableColumn("ii", "desc"): None,
                            TableColumn("ii", "coll"): None,
                            TableColumn("ii", "partial"): None}),
                        ConditionParameterSet(
                            MakeFieldParameterSetEnumerable(
                                {TableColumn('il', "name"): GetNotNullFieldParameter()})))
                    
                    query.GetCases().Add(
                        ConditionSet[IEnumValue[IndexKind], str](
                            "index_type",
                            EnumValue(IndexKind.Normal),
                            TableColumn("il", "origin"),
                            Dictionary[IEnumValue[IndexKind], IParameter[IOperand[str]]]({
                                EnumValue[IndexKind](IndexKind.PrimaryKey): FieldParameter[str].Create(Operator.Equals, "pk"),
                                EnumValue[IndexKind](IndexKind.Unique): FieldParameter[str].Create(Operator.Equals, "u")}))) # TODO: or il."unique" = 1
                    
                    query.GetJoins().Add(
                        Join(
                            JoinType.Inner,
                            "PRAGMA_INDEX_XINFO",
                            TableParameter[IColumn](
                                "ii",
                                MakeTableColumnIterable(
                                    TableColumn("il", "name"))),
                            ConditionParameterSet(
                                MakeFieldParameterSetEnumerable({
                                    TableColumn("ii", "key"): FieldParameter[int].Create(Operator.Equals, 1)}))))

                    # TODO: ORDER BY il.name, ii.seqno
                    
                    return query.Execute()

                indices: ISelectionQueryExecutionResult|None = executeQuery(connection)

                if indices is None:
                    return
                
                factory: IIndexFactory = connection.GetIndexFactory()
                indexName: str = ''
                result: Generator[IIndex]|None = None
                columns: Singly.IList[str] = Queue[str]()
                func: Callable[[IIndexFactory, str, str, IndexKind, str, Singly.IList[str]], Generator[IIndex]|None] = getParser()

                for row in indices.AsIterable():
                    if (result := func(factory, indexName, str(row[0]), IndexKind(row[6]), str(row[2]), columns)) is None:
                        continue

                    for index in result:
                        yield index
            
            def getForeignKeys(connection: IConnection) -> Generator[IIndex]:
                def executeQuery(connection: IConnection) -> ISelectionQueryExecutionResult|None:
                    query: ISelectionQuery = connection.GetQueryFactory().GetSelectionQuery(
                        TableParameterSet({
                            String("PRAGMA_FOREIGN_KEY_LIST"): TableParameter(
                                'fk', MakeTableValueIterable(self.GetName()))}),
                        ColumnParameterSet[IParameter[object]]({
                            TableColumn("fk", "id"): None,
                            TableColumn("fk", "seq"): None,
                            TableColumn("fk", "from"): None,
                            TableColumn("fk", "table"): None,
                            TableColumn("fk", "to"): None,
                            TableColumn("fk", "on_update"): None,
                            TableColumn("fk", "on_delete"): None,
                            TableColumn("fk", "match"): None}))

                        # TODO: ORDER BY fk.id, fk.seq
                    
                    return query.Execute()

                foreignKeys: ISelectionQueryExecutionResult|None = executeQuery(connection)

                if foreignKeys is None:
                    return
                
                factory: IIndexFactory = connection.GetIndexFactory()

                for row in foreignKeys.AsIterable():
                    yield factory.GetForeignKey(str(row[0]), str(row[2]), DualResult[str, str](str(row[3]), str(row[4])))

            return Append(getIndices(connection), getForeignKeys(connection))

        if self.__indices is None:
            self.__indices = self.__GetArray(getIndices)
        
        return self.__indices
    
    def Remove(self) -> None:
        self.__connection.Execute(f"DROP TABLE {self.GetName()}")
    
    def Dispose(self) -> None:
        self.__fields = None
        self.__connection.Dispose()

@final
class Connection(Abstract.Connection):
    def __GetTable(self, connection: sqlite3.Connection, name: str) -> Table:
        return Table(_Connection(self, connection), name)
    
    def __DoCreateTable(self, connection: sqlite3.Connection, query: str, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> None:
        connection.execute(f"CREATE TABLE {query}{self.FormatTableName(name)} ({", ".join(Select(Append(fields, indices), lambda item: self.FormatTableName(item.ToString())))}) STRICT")
    def __TryCreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> None:
        if self.__connection is None:
            raise GetDisposedError()
        
        self.__DoCreateTable(self.__connection, "IF NOT EXISTS ", name, fields, indices)

        return None
    def __CreateTable(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        if self.__connection is None:
            raise GetDisposedError()
        
        self.__DoCreateTable(self.__connection, '', name, fields, indices)

        return self.__GetTable(self.__connection, name)
    
    def __init__(self, path: str):
        super().__init__()

        self.__path: str = path
        self.__connection: sqlite3.Connection|None = None
    
    def Open(self) -> bool:
        self.__connection = sqlite3.connect(self.__path, autocommit = False)

        return True
    
    def FormatTableName(self, name: str) -> str:
        return DoubleQuoteSurround(name)
    
    def GetTableNames(self) -> Generator[str]:
        queryExecutionResult: ISelectionQueryExecutionResult|None = self.GetQueryFactory().GetSelectionQuery(
            TableParameterSet.Create(
                MakeSequence(
                    String("sqlite_master"))),
            ColumnParameterSet(
                {Column("name"): None}),
            ConditionParameterSet(
                MakeFieldParameterSetEnumerable(
                    {Column("type"): FieldParameter[str].Create(Operator.Equals, "table")}))).Execute()

        if queryExecutionResult is None:
            return

        for row in queryExecutionResult.AsIterable():
            yield str(row[0])
    
    @staticmethod
    def __EnsureFields(fields: Iterable[IField]) -> None:
        EnsureOnlyOne(fields, lambda field: field.GetAttributes() == FieldAttributes.AutoIncrement, f"The '{FieldAttributes.AutoIncrement.name}' must be set to at most one field.")
    
    def _TryCreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable|None:
        Connection.__EnsureFields(fields)

        self.__TryCreateTable(name, fields, indices)
    def _CreateTableOverride(self, name: str, fields: Iterable[IField], indices: Iterable[IIndex]|None) -> ITable:
        Connection.__EnsureFields(fields)
        
        return self.__CreateTable(name, fields, indices)

    def _GetTable(self, name: str) -> ITable:
        if self.__connection is None:
            raise GetDisposedError()
        
        return self.__GetTable(self.__connection, name)
    
    def _GetFieldFactory(self) -> IFieldFactory:
        return FieldFactory(self)
    def _GetQueryFactory(self) -> IQueryFactory:
        if self.__connection is None:
            raise GetDisposedError()
        
        return QueryFactory(self.__connection)
    def _GetIndexFactory(self) -> IIndexFactory:
        if self.__connection is None:
            raise GetDisposedError()
        
        return IndexFactory(self)
    
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