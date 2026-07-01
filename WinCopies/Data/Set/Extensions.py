from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Abstraction.Mapping import Dictionary
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, IteratorProvider, GetEmptyEnumerable, AsEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursiveEnumerationHandler, RecursivelyIterableProvider, CreateRecursivelyIterableProvider
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursiveEnumerator, StackedRecursiveEnumerator
from WinCopies.Collections.Expression import ICompositeExpression, ICompositeExpressionNode, IConnector, CompositeExpressionRoot, CompositeExpressionValueRoot, CreateCompositeExpressionRoot
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Loop import DoForEachItem
from WinCopies.Collections.Util import MakeSequence

from WinCopies.Delegates import Self

from WinCopies.String import StringifyIfNone

from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Delegate import Method, Selector, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Object import IValueProvider, IValueItem, IBoolean, IString, GetFalseObject
from WinCopies.Typing.Pairing import IKeyValuePair



from WinCopies.Data import ConditionalOperator, IColumn, Column, TableColumn, IOperand, IOperandValue
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IFormattable, IParameter, ITableParameter
from WinCopies.Data.QueryBuilder import IJoinBase, IConditionalQueryWriter, ISelectionQueryWriter, IParameterSetBase
from WinCopies.Data.Set import IFieldParameterSetItem, IFieldConditionSetItemAlias as IFieldConditionSetItem, IFieldParameterRecursivelyEnumerable, IFieldConditionRecursivelyEnumerableAlias as IFieldConditionRecursivelyEnumerable, IParameterSet, IColumnParameterSet, IFieldParameterSet, IFieldConditionSet, ITableParameterSet

class IConditionParameterSet(IParameterSetBase[IConditionalQueryWriter]):
    def __init__(self) -> None: super().__init__()

class IBranchSet[T: IValueProvider](IParameterSetBase[ISelectionQueryWriter]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetAlias(self) -> str:
        ...

    @abstractmethod
    def GetDefault(self) -> T:
        ...

class ICaseSet[TKey: IValueItem, TValue](IBranchSet[TKey]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IColumn:
        ...
    
    @abstractmethod
    def GetConditions(self) -> IDictionary[TKey, TValue]:
        ...

class IExistenceQuery(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        ...
    
    @abstractmethod
    def GetTableParameter(self) -> ITableParameter[object]|None:
        ...

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        ...

    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        ...
    @final
    def SetJoinsFromValues(self, *joins: IJoin) -> None:
        self.SetJoins(joins)

    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        ...
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        ...
class ExistenceQuery(IExistenceQuery):
    def __init__(self, tableName: str, tableParameter: ITableParameter[object]|None, conditions: IConditionParameterSet|None = None) -> None:
        super().__init__()

        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object]|None = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
        self.__joins: Iterable[IJoin]|None = None
    
    @final
    def GetTableName(self) -> str: return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]|None: return self.__tableParameter

    @final
    def GetJoins(self) -> Iterable[IJoin]|None: return self.__joins
    @final
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None: self.__joins = joins
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None: return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None: self.__conditions = conditions

class IExistenceSet(IBranchSet[IBoolean]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetQuery(self) -> IExistenceQuery:
        ...

class IMatchSet[T: IValueItem](ICaseSet[T, T]):
    def __init__(self) -> None: super().__init__()
class IConditionSet[TKey: IValueItem, TValue](ICaseSet[TKey, IParameter[IOperand[TValue]]]):
    def __init__(self) -> None: super().__init__()
class IIfSet[T: IValueItem](ICaseSet[T, IConditionParameterSet]):
    def __init__(self) -> None: super().__init__()

class ParameterSet[T](Dictionary[IColumn, T], IParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T]|None = None) -> None: super().__init__(dictionary)

class ColumnParameterSet[T: IFormattable](ParameterSet[T|None], IColumnParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T|None]|None = None) -> None: super().__init__(dictionary)

def AsColumns(columnNames: Iterable[str], tableName: str|None = None) -> Generator[IColumn]:
    return Select(columnNames, (lambda columnName: Column(columnName)) if tableName is None else (lambda columnName: TableColumn(tableName, columnName)))

def CreateColumnParameterSet(columns: Iterable[IColumn]) -> IColumnParameterSet[IFormattable]:
    return ColumnParameterSet[IFormattable](dict.fromkeys(columns))
def CreateColumnParameterSetFromNames(columnNames: Iterable[str], tableName: str|None = None) -> IColumnParameterSet[IFormattable]:
    return CreateColumnParameterSet(AsColumns(columnNames, tableName))

def MakeColumnParameterSet(*columns: IColumn) -> IColumnParameterSet[IFormattable]:
    return CreateColumnParameterSet(columns)
def MakeColumnParameterSetFromNames(tableName: str|None = None, *columnNames: str) -> IColumnParameterSet[IFormattable]:
    return CreateColumnParameterSetFromNames(columnNames, tableName)

def _TryGetConnector[TColumn: IColumn, TParameter: IParameter[IOperandValue]](connector: IConnector[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]|None) -> ConditionalOperator|None:
    return None if connector is None else connector.GetConnector()

@final
class _Expression[TColumn: IColumn, TParameter: IParameter[IOperandValue]](Abstract, IFieldParameterSetItem[TColumn, TParameter]):
    def __init__(self, expression: ICompositeExpression[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]) -> None:
        super().__init__()

        self.__expression: ICompositeExpression[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator] = expression
    
    def TryGetFieldParameter(self) -> IKeyValuePair[TColumn, TParameter|None]|None: return self.__expression.TryGetValue().TryGetValue()
    
    def TryGetPreviousOperator(self) -> ConditionalOperator|None: return _TryGetConnector(self.__expression.GetPrevious())
    def TryGetNextOperator(self) -> ConditionalOperator|None: return _TryGetConnector(self.__expression.GetNext())
    
    def TryGetItems(self) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]|None:
        expression: ICompositeExpressionNode[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]|None = self.__expression.TryGetItems()

        return None if expression is None else IteratorProvider[IFieldParameterSetItem[TColumn, TParameter]](lambda: Select(expression.AsIterable(), lambda expression: _Expression(expression)))

def _GetEnumerable[TColumn: IColumn, TParameter: IParameter[IOperandValue]](enumerationItems: IFieldParameterSetItem[TColumn, TParameter]) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]:
    items: IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]|None = enumerationItems.TryGetItems()

    return GetEmptyEnumerable() if items is None else items

class _RecursiveEnumerator[TColumn: IColumn, TParameter: IParameter[IOperandValue]](RecursiveEnumerator[IFieldParameterSetItem[TColumn, TParameter]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[TColumn, TParameter]], handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None = None) -> None:
        super().__init__(enumerator, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[TColumn, TParameter]) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]:
        return _GetEnumerable(enumerationItems)
class _StackedRecursiveEnumerator[TColumn: IColumn, TParameter: IParameter[IOperandValue]](StackedRecursiveEnumerator[IFieldParameterSetItem[TColumn, TParameter]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[TColumn, TParameter]], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None = None) -> None:
        super().__init__(enumerator, enumerationOrder, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[TColumn, TParameter]) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]:
        return _GetEnumerable(enumerationItems)

def _TryGetRecursiveEnumerator[TColumn: IColumn, TParameter: IParameter[IOperandValue]](enumerator: IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None:
    return None if enumerator is None else _RecursiveEnumerator(enumerator, handler)
def _TryGetRecursiveStackedEnumerator[TColumn: IColumn, TParameter: IParameter[IOperandValue]](enumerator: IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None, enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None:
    return None if enumerator is None or enumerationOrder == EnumerationOrder.Null else _StackedRecursiveEnumerator(enumerator, enumerationOrder, handler)

def _TryGetEnumerator[TColumn: IColumn, TParameter: IParameter[IOperandValue]](expressionRoot: IFieldParameterRecursivelyEnumerable[TColumn, TParameter], enumerationOrder: EnumerationOrder, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None:
    if enumerationOrder == EnumerationOrder.Null: return None
    
    match enumerationOrder:
        case EnumerationOrder.FIFO: return _TryGetRecursiveEnumerator(expressionRoot.TryGetEnumerator(), handler)
        case EnumerationOrder.LIFO: return expressionRoot.TryGetRecursiveStackedEnumerator(EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
        
        case _: raise ValueError(enumerationOrder)

class FieldParameterRecursivelyEnumerable[TColumn: IColumn, TParameter: IParameter[IOperandValue]](IFieldParameterRecursivelyEnumerable[TColumn, TParameter]):
    def __init__(self, items: IFieldParameterSet[TColumn, TParameter]) -> None:
        super().__init__()

        self.__items: IFieldParameterSet[TColumn, TParameter] = items
        self.__iterable: RecursivelyIterableProvider[IFieldParameterSetItem[TColumn, TParameter]] = CreateRecursivelyIterableProvider(self)
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[IFieldParameterSetItem[TColumn, TParameter]]: return self.__iterable.AsRecursivelyEnumerable()
    
    @final
    def AsIterable(self) -> Iterable[IFieldParameterSetItem[TColumn, TParameter]]: return self.__iterable.AsIterable()
    
    def TryGetEnumerator(self) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None: return AsEnumerator(Select(self.__items.AsIterable(), lambda expression: _Expression[TColumn, TParameter](expression)))
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None = None) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None: return _TryGetEnumerator(self, enumerationOrder, handler)
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[TColumn, TParameter]]|None = None) -> IEnumerator[IFieldParameterSetItem[TColumn, TParameter]]|None: return _TryGetRecursiveStackedEnumerator(self.TryGetEnumerator(), enumerationOrder, handler)

@final
class RecursivelyParameterEnumerableUpdater[TColumn: IColumn, TParameter: IParameter[IOperandValue]](ValueFunctionUpdater[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]]):
    def __init__(self, items: IFieldParameterSet[TColumn, TParameter], updater: Method[IFunction[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]]]) -> None:
        super().__init__(updater)

        self.__items: IFieldParameterSet[TColumn, TParameter] = items
    
    def _GetValue(self) -> IFieldParameterRecursivelyEnumerable[TColumn, TParameter]: return FieldParameterRecursivelyEnumerable[TColumn, TParameter](self.__items)

class FieldParameterNodeSet[TColumn: IColumn, TParameter: IParameter[IOperandValue]](CompositeExpressionRoot[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator], IFieldParameterSet[TColumn, TParameter]):
    def __init__(self, initialNode: ICompositeExpressionNode[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator]) -> None:
        def update(func: IFunction[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]]) -> None: self.__parameterEnumerable = func
        
        super().__init__(initialNode)

        self.__parameterEnumerable: IFunction[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]] = RecursivelyParameterEnumerableUpdater[TColumn, TParameter](self, update) # type: ignore[no-redef]
    
    @final
    def AsRecursivelyParameterEnumerable(self) -> IFieldParameterRecursivelyEnumerable[TColumn, TParameter]: return self.__parameterEnumerable.GetValue()
class FieldParameterSet[TColumn: IColumn, TParameter: IParameter[IOperandValue]](CompositeExpressionValueRoot[IKeyValuePair[TColumn, TParameter|None], ConditionalOperator], IFieldParameterSet[TColumn, TParameter]):
    def __init__(self, initialValue: IKeyValuePair[TColumn, TParameter|None]) -> None:
        def update(func: IFunction[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]]) -> None: self.__parameterEnumerable = func
        
        super().__init__(initialValue)

        self.__parameterEnumerable: IFunction[IFieldParameterRecursivelyEnumerable[TColumn, TParameter]] = RecursivelyParameterEnumerableUpdater[TColumn, TParameter](self, update) # type: ignore[no-redef]
    
    @final
    def AsRecursivelyParameterEnumerable(self) -> IFieldParameterRecursivelyEnumerable[TColumn, TParameter]: return self.__parameterEnumerable.GetValue()

class FieldConditionNodeSet[T: IColumn](FieldParameterNodeSet[T, IParameter[IOperandValue]], IFieldConditionSet[T]):
    def __init__(self, initialNode: ICompositeExpressionNode[IKeyValuePair[T, IParameter[IOperandValue]|None], ConditionalOperator]) -> None: super().__init__(initialNode)
class FieldConditionSet[T: IColumn](FieldParameterSet[T, IParameter[IOperandValue]], IFieldConditionSet[T]):
    def __init__(self, initialValue: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> None: super().__init__(initialValue)

def __CreateFieldParameterSet[T: IColumn](conditionalOperator: ConditionalOperator, conditions: Iterable[IKeyValuePair[T, IParameter[IOperandValue]|None]]) -> IFieldConditionSet[T]|None:
    return CreateCompositeExpressionRoot(lambda condition: FieldConditionSet[T](condition), Self, conditionalOperator, conditions)

def CreateFieldParameterConjunctionSet[T: IColumn](conditions: Iterable[IKeyValuePair[T, IParameter[IOperandValue]|None]]) -> IFieldConditionSet[T]|None:
    return __CreateFieldParameterSet(ConditionalOperator.And, conditions)
def CreateFieldParameterDisjunctionSet[T: IColumn](conditions: Iterable[IKeyValuePair[T, IParameter[IOperandValue]|None]]) -> IFieldConditionSet[T]|None:
    return __CreateFieldParameterSet(ConditionalOperator.Or, conditions)

def MakeFieldParameterConjunctionSet[T: IColumn](*conditions: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> IFieldConditionSet[T]|None:
    return CreateFieldParameterConjunctionSet(conditions)
def MakeFieldParameterDisjunctionSet[T: IColumn](*conditions: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> IFieldConditionSet[T]|None:
    return CreateFieldParameterDisjunctionSet(conditions)

class TableParameterSet(Dictionary[IString, ITableParameter[object]|None], ITableParameterSet):
    def __init__(self, dictionary: dict[IString, ITableParameter[object]|None]|None = None) -> None: super().__init__(dictionary)
    
    @staticmethod
    def Create(tableNames: Iterable[IString]) -> ITableParameterSet:
        return TableParameterSet(dict[IString, None].fromkeys(tableNames))
    @staticmethod
    def CreateFromNames(*tableNames: IString) -> ITableParameterSet:
        return TableParameterSet.Create(tableNames)

@final
class _ConditionParameterSetHandler[T: IColumn](RecursiveEnumerationHandler[IFieldConditionSetItem[T]]):
    def __init__(self, writer: IConditionalQueryWriter, action: Method[IFieldConditionSetItem[T]], connectorHandlerUpdater: Method[Method[IFieldConditionSetItem[T]]]) -> None:
        super().__init__()

        self.__writer: IConditionalQueryWriter = writer
        self.__action: Method[IFieldConditionSetItem[T]] = action
        self.__connectorHandlerUpdater: Method[Method[IFieldConditionSetItem[T]]] = connectorHandlerUpdater
    
    def OnEnteringEnumerationLevel(self, item: IFieldConditionSetItem[T]) -> None:
        # The recursive enumeration fires an enter/exit level around every item (see
        # RecursiveEnumeratorBase), so each condition is its own level; the connector to the
        # previous sibling is carried by the item itself and is written before its parentheses.
        operator: ConditionalOperator|None = item.TryGetPreviousOperator()

        if operator is not None: self.__writer.Write(f" {operator} ")

        self.__writer.Write('(')

        self.__connectorHandlerUpdater(self.__action)
    def OnExitingEnumerationLevel(self, cookie: None) -> None: self.__writer.Write(')')

class ConditionParameterSet[T: IColumn](IConditionParameterSet):
    def __init__(self, set: IFieldConditionRecursivelyEnumerable[T]) -> None:
        super().__init__()

        self.__set: IFieldConditionRecursivelyEnumerable[T] = set
    
    @final
    def Render(self, writer: IConditionalQueryWriter) -> bool:
        value: IKeyValuePair[T, IParameter[IOperandValue]|None]|None = None
        action: Method[IFieldConditionSetItem[T]] = lambda _: None

        def updateAction(_action: Method[IFieldConditionSetItem[T]]) -> None:
            nonlocal action

            action = _action
        def process(condition: IFieldConditionSetItem[T]) -> None:
            def write(value: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> None: writer.Write(writer.ProcessConditionValue(value.GetKey(), value.GetValue()))

            nonlocal value

            if (value := condition.TryGetFieldParameter()) is not None: write(value)

        return DoForEachItem(self.__set.GetRecursiveEnumerable(handler = _ConditionParameterSetHandler[T](writer, process, updateAction)).AsIterable(), lambda item: action(item))

def CreateConditionSetFromConditions[T: IColumn](set: IFieldConditionRecursivelyEnumerable[T]) -> IConditionParameterSet:
    return ConditionParameterSet[T](set)
def TryCreateConditionSetFromConditions[T: IColumn](set: IFieldConditionRecursivelyEnumerable[T]|None) -> IConditionParameterSet|None:
    return None if set is None else CreateConditionSetFromConditions(set)

def CreateConditionSet[T: IColumn](set: IFieldConditionSet[T]) -> IConditionParameterSet:
    return CreateConditionSetFromConditions(set.AsRecursivelyParameterEnumerable())
def TryCreateConditionSet[T: IColumn](set: IFieldConditionSet[T]|None) -> IConditionParameterSet|None:
    return None if set is None else CreateConditionSet(set)

def CreateConjunctionSet[T: IColumn](conditions: Iterable[IKeyValuePair[T, IParameter[IOperandValue]|None]]) -> IConditionParameterSet|None:
    return TryCreateConditionSet(CreateFieldParameterConjunctionSet(conditions))
def CreateDisjunctionSet[T: IColumn](conditions: Iterable[IKeyValuePair[T, IParameter[IOperandValue]|None]]) -> IConditionParameterSet|None:
    return TryCreateConditionSet(CreateFieldParameterDisjunctionSet(conditions))

def MakeConjunctionSet[T: IColumn](*conditions: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> IConditionParameterSet|None:
    return CreateConjunctionSet(conditions)
def MakeDisjunctionSet[T: IColumn](*conditions: IKeyValuePair[T, IParameter[IOperandValue]|None]) -> IConditionParameterSet|None:
    return CreateDisjunctionSet(conditions)

class BranchSetBase[T: IValueProvider](Abstract, IBranchSet[T]):
    def __init__(self, alias: str) -> None:
        super().__init__()

        self.__alias: str = alias
    
    @final
    def GetAlias(self) -> str: return self.__alias
    
    @abstractmethod
    def _GetColumn(self) -> str|None:
        ...

    @abstractmethod
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        ...
    
    @final
    def Render(self, writer: ISelectionQueryWriter) -> bool:
        def getColumnName() -> str:
            columnName: str = StringifyIfNone(self._GetColumn())

            return '' if columnName == '' else ' ' + columnName
        
        writer.Write(f"CASE{getColumnName()}")
        
        self._WriteConditions(writer)
        
        writer.Write(f" ELSE {writer.JoinParameters(MakeSequence(self.GetDefault().GetUnderlyingValue()))} END AS {writer.FormatTableName(self.GetAlias())}")

        return True
class BranchSet[T: IValueProvider](BranchSetBase[T]):
    def __init__(self, alias: str, defaultValue: T) -> None:
        super().__init__(alias)

        self.__defaultValue: T = defaultValue
    
    @final
    def GetDefault(self) -> T: return self.__defaultValue

class ExistenceSet(BranchSetBase[IBoolean], IExistenceSet):
    def __init__(self, alias: str, query: IExistenceQuery) -> None:
        super().__init__(alias)

        self.__query: IExistenceQuery = query
    
    @final
    def _GetColumn(self) -> None:
        return None
    
    @final
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        query: IExistenceQuery = self.GetQuery()

        writer.Write(f" WHEN (SELECT 1 FROM {writer.AddTable(query.GetTableName(), query.GetTableParameter())}")

        writer.AddJoins(query.GetJoins())
        writer.AddConditions(query.GetConditions())

        writer.Write(") THEN 1")
    
    @final
    def GetDefault(self) -> IBoolean: return GetFalseObject()
    
    @final
    def GetQuery(self) -> IExistenceQuery: return self.__query

class CaseSet[TKey: IValueItem, TValue](BranchSet[TKey], ICaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, conditions: IDictionary[TKey, TValue]|None = None) -> None:
        super().__init__(alias, defaultValue)

        self.__column: IColumn = column
        self.__conditions: IDictionary[TKey, TValue] = Dictionary[TKey, TValue]() if conditions is None else conditions
    
    @abstractmethod
    def _RenderValue(self, value: TValue, writer: ISelectionQueryWriter) -> None:
        ...

    @final
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        def render(item: IKeyValuePair[TKey, TValue]) -> None:
            writer.Write(" WHEN ")

            self._RenderValue(item.GetValue(), writer)

            writer.Write(f" THEN {writer.JoinParameters(MakeSequence(item.GetKey().GetUnderlyingValue()))}")

        if not DoForEachItem(self.GetConditions().AsIterable(), render): raise ValueError("No condition given.")
    
    @final
    def GetColumn(self) -> IColumn: return self.__column
    
    @final
    def GetConditions(self) -> IDictionary[TKey, TValue]: return self.__conditions

class MatchSet[T: IValueItem](CaseSet[T, T], IMatchSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, T]|None = None) -> None: super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> str:
        return f"{self.GetColumn()}"
    
    @final
    def _RenderValue(self, value: T, writer: ISelectionQueryWriter) -> None:
        writer.Write(writer.JoinParameters(MakeSequence(value)))

class ConditionalSet[TKey: IValueItem, TValue](CaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, dictionary: IDictionary[TKey, TValue]|None = None) -> None: super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> None:
        return None

class ConditionSet[TKey: IValueItem, TValue](ConditionalSet[TKey, IParameter[IOperand[TValue]]], IConditionSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, dictionary: IDictionary[TKey, IParameter[IOperand[TValue]]]|None = None) -> None: super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IParameter[IOperand[TValue]], writer: ISelectionQueryWriter) -> None:
        def getArgument(arguments: Iterable[IOperand[TValue]]) -> Generator[IOperand[TValue]]:
            func: Selector[IOperand[TValue]]|None = None

            def getArgument(argument: IOperand[TValue]) -> IOperand[TValue]:
                nonlocal func

                def throw(_: IOperand[TValue]) -> IOperand[TValue]: raise InvalidOperationError("Only one argument must be given in Case statements.")

                func = throw

                return argument
            
            func = getArgument

            for argument in arguments: yield func(argument)
        
        writer.Write(value.Format(self.GetColumn().ToString(writer.FormatTableName), writer.JoinOperands(getArgument(value.AsIterable()))))
class IfSet[T: IValueItem](ConditionalSet[T, IConditionParameterSet], IIfSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, IConditionParameterSet]|None = None) -> None: super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IConditionParameterSet, writer: ISelectionQueryWriter) -> None:
        value.Render(writer)

class IJoin(IJoinBase[IConditionParameterSet]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        ...
class Join(IJoin):
    def __init__(self, type: JoinType, tableName: str, tableParameter: ITableParameter[object], conditions: IConditionParameterSet|None = None) -> None:
        super().__init__()

        self.__type: JoinType = type
        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object] = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
    
    @final
    def GetType(self) -> JoinType: return self.__type
    
    @final
    def GetTableName(self) -> str: return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]: return self.__tableParameter
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None: return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None: self.__conditions = conditions