from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum
from types import TracebackType
from typing import overload, final, Callable, Any, Type, cast



from WinCopies import IInterface, IDisposable, Abstract

from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Abstraction.Collection import CreateTuple, MakeTuple, CreateHashableTuple
from WinCopies.Collections.Abstraction.Mapping import Set, Dictionary, CreateSet, CreateDictionary
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateKeyedSet
from WinCopies.Collections.Core import ICountable, IContainer, IReadOnlyIndexable
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, EnumeratorBase, Enumerable, GetEmptyEnumerable, AsEnumerator, GetEnumeratorInactiveError, CreateIteratorProvider
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursiveStackedEnumerationHandler, RecursivelyIterableProvider, CreateRecursivelyIterableProvider
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursivelyEnumerable, RecursiveEnumerator, StackedRecursiveEnumerator
from WinCopies.Collections.Expression import IConnector, ICompositeExpression, ICompositeExpressionNodeBase, ICompositeExpressionNode, ICompositeExpressionRoot, CompositeExpressionValueNode, CompositeExpressionNode, CompositeExpressionValueRoot, CompositeExpressionRoot
from WinCopies.Collections.Extensions import ITuple, IHashableTuple, IReadOnlySet, IReadOnlyDictionary, ISet, IKeyedSet, IDictionary
from WinCopies.Collections.Iteration import Any as HasAny, AppendItem, Concatenate as ConcatenateIterables, ConcatenateValues, ConcatenateItems, ConcatenateEnumerables, GetFirstOfType, Include, Exclude, Select, Match, SelectWhereNotNone, WhereSelect, WhereOfType, WhereNotOfType
from WinCopies.Collections.Iteration.Loop import DoForEachItem
from WinCopies.Collections.Linked.Singly import IEnumerableList, ICountableEnumerableList, EnumerableQueue, CountableEnumerableQueue
from WinCopies.Collections.Loop import DoForEachItem as DoForEach, Scan
from WinCopies.Collections.Util import MakeSequence

from WinCopies.Delegates import BoolTrue, NoAction, GetTruthyPredicate

from WinCopies.Typing import IDisposable, IMonitor, Monitor, Error, InvalidOperationError
from WinCopies.Typing.Delegate import Action, Method, Function, Predicate, Converter, Selector, IFunction, IMethodBase, IInitializableConverter, ValueFunction, ValueFunctionUpdater, ValueConverterUpdater
from WinCopies.Typing.Object import IItem, IValueItem, IValueObject, IItemObject, IReference, Reference, DefaultReference, IString, String, IType, Type as TypeObject, Map
from WinCopies.Typing.Pairing import IKeyValuePair, CreateKeyValuePair, CreateDualResult
from WinCopies.Typing.Reflection import GetterBase, SetterBase, Property, IFunctionProvider, IGetterProvider, IPropertyProvider, IReadOnlyPropertyBase, IReadOnlyProperty, IProperty, ReadOnlyPropertyDecoratorBase, PropertyDecorator, GetTypeName



from WinCopies.Data import Operator, ConditionalOperator, IOperandValue, IOperand, ITableColumn, Operand, SetOperand, GetActiveTransactionError
from WinCopies.Data.Abstract import IConnection, ITransactionControl, ITable
from WinCopies.Data.Parameter import IFormattable, IParameter, FieldParameter, CreateFieldParameterFromValue
from WinCopies.Data.Query import ISelectionQuery, ISelectionQueryExecutionResult, IInsertionQueryExecutionResult, IQueryExecutionResult
from WinCopies.Data.Set import IColumnParameterSet, IFieldConditionRecursivelyEnumerable, IFieldParameterSetItem
from WinCopies.Data.Set.Extensions import IConditionParameterSet, TableParameterSet, CreateColumnParameterSet, TryCreateConditionSetFromConditions, CreateConjunctionSet

class EntityInsertionError(Error):
    def __init__(self, message: str) -> None: super().__init__(message)

class DuplicateIdentityError(EntityInsertionError):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"An entity with the same identity is already tracked for {GetTypeName(value)}.")
class ForeignKeyCycleError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"Foreign key cycle detected involving {GetTypeName(value)}.")

class EntityNotPersistedError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"The entity of type {GetTypeName(value)} is not persisted and cannot be updated.")
class UnpersistedReferenceError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"The entity references an unpersisted entity of type {GetTypeName(value)}; it must be persisted before the referencing entity can be updated.")
class PrimaryKeyMutationError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"The primary key of an entity of type {GetTypeName(value)} cannot be mutated.")
class RowVanishedError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"The row backing an entity of type {GetTypeName(value)} no longer exists in the database (database/memory invariant violation).")
class UnresolvedRollbackError(Error):
    def __init__(self) -> None: super().__init__("The data context has an unresolved rollback; call Reverse() or Retry() before performing any further database operation.")
class DeletedEntityError(Error):
    def __init__(self, value: Type[Entity]|Entity) -> None: super().__init__(f"The entity of type {GetTypeName(value)} has been deleted and can no longer be used.")

@final
class _TableColumn(Abstract, ITableColumn):
    def __init__(self, columnName: str, tableName: str) -> None:
        super().__init__()

        self.__columnName: str = columnName
        self.__tableName: str = tableName
    
    def GetColumnName(self) -> str: return self.__columnName
    
    def GetTableName(self) -> str: return self.__tableName

@final
class _ColumnParameterUpdater(ValueConverterUpdater[str, ITableColumn]):
    def __init__(self, parameter: IColumnParameterAbstract, updater: Method[IInitializableConverter[str, ITableColumn]]) -> None:
        super().__init__(updater)

        self.__parameter: IColumnParameterAbstract = parameter
    
    def ConvertValue(self, value: str) -> ITableColumn: return _TableColumn(self.__parameter.GetColumnName(), value)
@final
class _ForeignKeyParameterUpdater(ValueConverterUpdater[str, ITuple[ITableColumn]]):
    def __init__(self, columnNames: Iterable[str], updater: Method[IInitializableConverter[str, ITuple[ITableColumn]]]) -> None:
        super().__init__(updater)

        self.__columnNames: Iterable[str] = columnNames
    
    def ConvertValue(self, value: str) -> ITuple[ITableColumn]: return CreateTuple(Select(self.__columnNames, lambda columnName: _TableColumn(columnName, value)))

class IColumnParameterCookie(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _AsColumn(self, tableName: str) -> ITableColumn:
        ...

class _IDataParameter(IKeyValuePair[IColumnParameterCookie, IParameter[IOperandValue]|None]):
    def __init__(self) -> None: super().__init__()

class _ParameterBase[T](Abstract, _IDataParameter):
    def __init__(self, cookie: IColumnParameterCookie, operand: IOperand[T]) -> None:
        super().__init__()

        self.__columnParameter: IColumnParameterCookie = cookie
        self.__parameter: IParameter[IOperandValue] = FieldParameter[T](operand)
    
    def IsKeyValuePair(self) -> bool: return False
    
    def GetKey(self) -> IColumnParameterCookie: return self.__columnParameter
    def GetValue(self) -> IParameter[IOperandValue]|None: return self.__parameter

@final
class _Parameter[T](_ParameterBase[T]):
    def __init__(self, cookie: IColumnParameterCookie, operator: Operator, value: T) -> None: super().__init__(cookie, Operand[T](operator, value))
@final
class _SetParameter[T: IValueItem](_ParameterBase[IReadOnlySet[T]]):
    def __init__(self, cookie: IColumnParameterCookie, values: IReadOnlySet[T]) -> None: super().__init__(cookie, SetOperand[T](values))

class _INode(ICompositeExpressionNode[_IDataParameter, ConditionalOperator]):
    def __init__(self) -> None: super().__init__()
class _IRoot(ICompositeExpressionRoot[_IDataParameter, ConditionalOperator]):
    def __init__(self) -> None: super().__init__()

@final
class _ValueNode(CompositeExpressionValueNode[_IDataParameter, ConditionalOperator], _INode):
    def __init__(self, parameter: _IDataParameter) -> None: super().__init__(parameter)
@final
class _Node(CompositeExpressionNode[_IDataParameter, ConditionalOperator], _INode):
    def __init__(self, node: _INode) -> None: super().__init__(node)

@final
class _ValueRoot(CompositeExpressionValueRoot[_IDataParameter, ConditionalOperator], _IRoot):
    def __init__(self, parameter: _IDataParameter) -> None: super().__init__(parameter)
@final
class _Root(CompositeExpressionRoot[_IDataParameter, ConditionalOperator], _IRoot):
    def __init__(self, x: _INode) -> None: super().__init__(x)

type ValueNode = _ValueNode
type Node = _Node

type ValueRoot = _ValueRoot
type Root = _Root

def Concatenate(x: _IDataParameter, operator: ConditionalOperator, y: _IDataParameter) -> _ValueNode:
    node: _ValueNode = _ValueNode(x)

    node.GetFirst().SetNext(operator, y)

    return node
def ConcatenateNode(x: _INode, operator: ConditionalOperator, y: _IDataParameter) -> _Node:
    node: _Node = _Node(x)

    node.GetFirst().SetNext(operator, y)

    return node
def ConcatenateNodes(x: _INode, operator: ConditionalOperator, y: _INode) -> _Node:
    node: _Node = _Node(x)

    node.GetFirst().SetNextExpression(operator, y)

    return node

def ConcatenateAsRoot(x: _IDataParameter, operator: ConditionalOperator, y: _IDataParameter) -> _ValueRoot:
    root: _ValueRoot = _ValueRoot(x)

    root.GetFirst().SetNext(operator, y)

    return root
def ConcatenateNodeAsRoot(x: _INode, operator: ConditionalOperator, y: _IDataParameter) -> _Root:
    root: _Root = _Root(x)

    root.GetFirst().SetNext(operator, y)

    return root
def ConcatenateNodesAsRoot(x: _INode, operator: ConditionalOperator, y: _INode) -> _Root:
    root: _Root = _Root(x)

    root.GetFirst().SetNextExpression(operator, y)

    return root

def _TryGetConnector(connector: IConnector[_IDataParameter, ConditionalOperator]|None) -> ConditionalOperator|None: return None if connector is None else connector.GetConnector()

@final
class _Expression(Abstract, IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]):
    def __init__(self, expression: ICompositeExpression[_IDataParameter, ConditionalOperator], tableName: str) -> None:
        super().__init__()

        self.__expression: ICompositeExpression[_IDataParameter, ConditionalOperator] = expression
        self.__tableName: str = tableName
    
    def TryGetFieldParameter(self) -> IKeyValuePair[ITableColumn, IParameter[IOperandValue]|None]|None:
        parameter: _IDataParameter|None = self.__expression.TryGetValue().TryGetValue()

        return None if parameter is None else CreateKeyValuePair(parameter.GetKey()._AsColumn(self.__tableName), parameter.GetValue()) # pyright: ignore[reportPrivateUsage]
    
    def TryGetPreviousOperator(self) -> ConditionalOperator|None: return _TryGetConnector(self.__expression.GetPrevious())
    def TryGetNextOperator(self) -> ConditionalOperator|None: return _TryGetConnector(self.__expression.GetNext())
    
    def TryGetItems(self) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        expression: ICompositeExpressionNode[_IDataParameter, ConditionalOperator]|None = self.__expression.TryGetItems()

        return None if expression is None else CreateIteratorProvider(lambda: Select(expression.AsIterable(), lambda expression: _Expression(expression, self.__tableName)))

def _GetEnumerable(enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
    items: IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = enumerationItems.TryGetItems()

    return GetEmptyEnumerable() if items is None else items

@final
class _RecursiveEnumerator(RecursiveEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]], handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> None: super().__init__(enumerator, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]: return _GetEnumerable(enumerationItems)
@final
class _StackedRecursiveEnumerator(StackedRecursiveEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> None: super().__init__(enumerator, enumerationOrder, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]: return _GetEnumerable(enumerationItems)

def _TryGetRecursiveEnumerator(enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None: return None if enumerator is None else _RecursiveEnumerator(enumerator, handler)
def _TryGetRecursiveStackedEnumerator(enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None, enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None: return None if enumerator is None or enumerationOrder == EnumerationOrder.Null else _StackedRecursiveEnumerator(enumerator, enumerationOrder, handler)

def _TryGetEnumerator(expressionRoot: IFieldConditionRecursivelyEnumerable[ITableColumn], enumerationOrder: EnumerationOrder, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
    if enumerationOrder == EnumerationOrder.Null: return None
    
    match enumerationOrder:
        case EnumerationOrder.FIFO: return _TryGetRecursiveEnumerator(expressionRoot.TryGetEnumerator(), handler)
        case EnumerationOrder.LIFO: return expressionRoot.TryGetRecursiveStackedEnumerator(EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())

        case _: raise ValueError(enumerationOrder)

@final
class _Set(Abstract, IFieldConditionRecursivelyEnumerable[ITableColumn]):
    def __init__(self, conditions: _IRoot, tableName: str) -> None:
        super().__init__()

        self.__conditions: _IRoot = conditions
        self.__tableName: str = tableName
        self.__iterable: RecursivelyIterableProvider[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]] = CreateRecursivelyIterableProvider(self)
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]: return self.__iterable.AsRecursivelyEnumerable()
    
    @final
    def AsIterable(self) -> Iterable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]: return self.__iterable.AsIterable()
    
    def TryGetEnumerator(self) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None: return AsEnumerator(Select(self.__conditions.AsIterable(), lambda expression: _Expression(expression, self.__tableName)))
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None: return _TryGetEnumerator(self, enumerationOrder, handler)
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None: return _TryGetRecursiveStackedEnumerator(self.TryGetEnumerator(), enumerationOrder, handler)

class Role(Enum):
    Null = 0
    PrimaryKey = 1
    ForeignKey = 2

class IColumnCondition[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToConditionParameter(self, operator: Operator, value: T) -> _IDataParameter|_ValueNode:
        ...
    @abstractmethod
    def ToConditionNode(self, operator: Operator, value: T) -> _ValueNode:
        ...
    @abstractmethod
    def ToConditionRoot(self, operator: Operator, value: T) -> _ValueRoot:
        ...
class IColumnSetCondition[T](IColumnCondition[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[T]]) -> _IDataParameter|_ValueNode:
        ...
    @abstractmethod
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[T]]) -> _ValueNode:
        ...
    @abstractmethod
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[T]]) -> _ValueRoot:
        ...

class IColumnParameterAbstract(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumnRole(self) -> Role:
        ...
    
    @abstractmethod
    def GetColumnName(self) -> str:
        ...
    
    @abstractmethod
    def _SetTableName(self, tableName: str) -> None:
        ...
class IEntityColumnParameterAbstract(IColumnParameterAbstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[Entity]:
        ...

class IColumnParameterBase(IColumnParameterAbstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _AsColumn(self, tableName: str) -> ITableColumn:
        ...
class IEntityColumnParameterBase(IColumnParameterBase, IEntityColumnParameterAbstract):
    def __init__(self) -> None: super().__init__()

class IColumnParameter[T](IColumnSetCondition[T], IColumnParameterBase):
    def __init__(self) -> None: super().__init__()
class IEntityColumnParameter[T: Entity](IColumnCondition[T], IEntityColumnParameterBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        ...

class IForeignKeyParameterAbstract(IEntityColumnParameterAbstract):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetColumnRole(self) -> Role: return Role.ForeignKey
class IForeignKeyParameterBase(IForeignKeyParameterAbstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _AsColumns(self, tableName: str) -> ITuple[ITableColumn]:
        ...
class IForeignKeyParameter[T: Entity](IForeignKeyParameterBase, IColumnCondition[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        ...

class IParameterKey(IReference[IColumnParameterAbstract]):
    def __init__(self) -> None: super().__init__()
class ParameterKey(Reference[IColumnParameterAbstract], IParameterKey):
    def __init__(self, parameter: IColumnParameterAbstract) -> None: super().__init__(parameter)
    
    def ToString(self) -> str: return self.GetValue().GetColumnName()

def _GetColumns(value: Type[Entity]|Entity) -> _Columns: return value._GetColumns() # pyright: ignore[reportPrivateUsage]

def _GetPrimaryKeys(value: Type[Entity]|Entity) -> ITuple[IDefaultColumn]: return _GetColumns(value).GetPrimaryKeys()

class IColumnParameterDelegate[TValue](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode:
        ...
    @abstractmethod
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        ...
    @abstractmethod
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot:
        ...
    
    @abstractmethod
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter|_ValueNode:
        ...
    @abstractmethod
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode:
        ...
    @abstractmethod
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot:
        ...
class ColumnParameterDelegateBase[TValue](Abstract, IColumnParameterDelegate[TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetCookie(self, index: int) -> IColumnParameterCookie:
        ...
    
    @abstractmethod
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        ...
    
    @final
    def _GetParameter(self, operator: Operator, entity: Entity, index: int, primaryKeys: IReadOnlyIndexable[IDefaultColumn]) -> _IDataParameter: return _Parameter[object](self._GetCookie(index), operator, primaryKeys.GetAt(index)._GetEntityValue(entity)) # pyright: ignore[reportPrivateUsage]

    @final
    def __ToCondition[TNode: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator]](self, operator: Operator, entity: Entity, selector: Callable[[_IDataParameter, ConditionalOperator, _IDataParameter], TNode]) -> _IDataParameter|TNode:
        def getParameter(index: int) -> _IDataParameter: return self._GetParameter(operator, entity, index, primaryKeys)

        primaryKeys: ITuple[IDefaultColumn] = _GetPrimaryKeys(entity)
        count: int = primaryKeys.GetCount()

        if count < 1: raise InvalidOperationError("No primary key found.")

        parameter: _IDataParameter = getParameter(0)

        if count > 1:
            node: TNode = selector(parameter, ConditionalOperator.And, getParameter(1))
            
            if count > 2: self._ToForeignKeyCondition(operator, entity, primaryKeys, node, count)

            return node

        return parameter
    
    @final
    def _ToConditionParameter(self, operator: Operator, entity: Entity) -> _IDataParameter|_ValueNode:
        return self.__ToCondition(operator, entity, Concatenate)
    @final
    def _ToConditionRoot(self, operator: Operator, entity: Entity) -> _ValueRoot:
        result: _IDataParameter|_ValueRoot = self.__ToCondition(operator, entity, ConcatenateAsRoot)

        return result if isinstance(result, _ValueRoot) else _ValueRoot(result)
    
    @final
    def __ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter:
        return _Parameter[TValue](self._GetCookie(0), operator, value)
    @final
    def __ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter:
        return _SetParameter[IValueObject[TValue]](self._GetCookie(0), values)
    
    @overload
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter:
        ...
    @overload
    def ToConditionParameter(self, operator: Operator, value: Entity) -> _IDataParameter|_ValueNode:
        ...
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue|Entity) -> _IDataParameter|_ValueNode: return self._ToConditionParameter(operator, value) if isinstance(value, Entity) else self.__ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        def toConditionNode(entity: Entity) -> _ValueNode:
            result: _IDataParameter|_ValueNode = self.ToConditionParameter(operator, entity)

            return result if isinstance(result, _ValueNode) else _ValueNode(result)
        
        return toConditionNode(value) if isinstance(value, Entity) else _ValueNode(self.__ToConditionParameter(operator, value))
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot: return self._ToConditionRoot(operator, value) if isinstance(value, Entity) else _ValueRoot(self.__ToConditionParameter(operator, value))
    
    @final
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter: return self.__ToSetConditionParameter(values)
    @final
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode: return _ValueNode(self.__ToSetConditionParameter(values))
    @final
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot: return _ValueRoot(self.__ToSetConditionParameter(values))

class ColumnParameterDelegate[TValue](ColumnParameterDelegateBase[TValue]):
    def __init__(self, cookie: IColumnParameterCookie) -> None:
        super().__init__()

        self.__cookie: IColumnParameterCookie = cookie
    
    @final
    def _GetCookie(self, index: int) -> IColumnParameterCookie: return self.__cookie
    
    @final
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        raise InvalidOperationError(f"Multiple primary keys found. The {foreignKeyConfig.__name__} decorator must be applied.")
class ForeignKeyParameterDelegate[TValue: Entity](ColumnParameterDelegateBase[TValue]):
    def __init__(self, cookieProvider: IColumnParameterCookieProvider) -> None:
        super().__init__()

        self.__cookieProvider: IColumnParameterCookieProvider = cookieProvider
    
    @final
    def _GetCookie(self, index: int) -> IColumnParameterCookie: return self.__cookieProvider.GetAt(index)
    
    @final
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        def concatenate(node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], index: int) -> None: node.GetFirst().SetNext(ConditionalOperator.And, self._GetParameter(operator, entity, index, primaryKeys))
        
        for i in range(2, count): concatenate(node, i)

class IEntityValueConfig[T: Entity](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        ...

class IColumnConfigBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetRole(self) -> Role:
        ...
    
    @abstractmethod
    def GetName(self) -> str|None:
        ...

class IColumnConfig(IColumnConfigBase):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetRole(self) -> Role: return Role.Null

class IPrimaryKeyConfig(IColumnConfigBase):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetRole(self) -> Role: return Role.PrimaryKey
class IEntityColumnConfig[T: Entity](IEntityValueConfig[T], IColumnConfigBase):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetRole(self) -> Role: return Role.ForeignKey

class IForeignKeyConfig[T: Entity](IEntityValueConfig[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetRole(self) -> Role: return Role.ForeignKey
    
    @abstractmethod
    def GetNames(self) -> IReadOnlyDictionary[IParameterKey, str|None]:
        ...

class EntityValueConfig[T: Entity](Abstract, IEntityValueConfig[T]):
    def __init__(self, t: Type[T]) -> None:
        super().__init__()

        self.__type: Type[T] = t
    
    @final
    def GetType(self) -> Type[T]: return self.__type

class ColumnConfigBase(Abstract, IColumnConfigBase):
    def __init__(self, name: str|None) -> None:
        super().__init__()

        self.__name: str|None = name
    
    @final
    def GetName(self) -> str|None: return self.__name

class ColumnConfig(ColumnConfigBase, IColumnConfig):
    def __init__(self, name: str|None) -> None: super().__init__(name)

class PrimaryKeyConfig(ColumnConfigBase, IPrimaryKeyConfig):
    def __init__(self, name: str|None) -> None: super().__init__(name)
class EntityColumnConfig[T: Entity](EntityValueConfig[T], IEntityColumnConfig[T]):
    def __init__(self, t: Type[T], name: str|None) -> None:
        super().__init__(t)

        self.__name: str|None = name
    
    @final
    def GetName(self) -> str|None: return self.__name

class ForeignKeyConfig[T: Entity](EntityValueConfig[T], IForeignKeyConfig[T]):
    def __init__(self, t: Type[T], columns: IReadOnlyDictionary[IParameterKey, str|None]) -> None:
        super().__init__(t)

        self.__columns: IReadOnlyDictionary[IParameterKey, str|None] = columns
    
    @final
    def GetNames(self) -> IReadOnlyDictionary[IParameterKey, str|None]: return self.__columns

class ColumnParameterAbstract(Abstract, IColumnParameterAbstract):
    @final
    class _ColumnProvider(Abstract, IColumnParameterCookie):
        def __init__(self, parameter: ColumnParameterAbstract) -> None:
            super().__init__()

            self.__parameter: ColumnParameterAbstract = parameter
        
        def _AsColumn(self, tableName: str) -> ITableColumn: return self.__parameter._AsColumn(tableName)
    
    def __init__(self, role: Role, name: str) -> None:
        def update(converter: IInitializableConverter[str, ITableColumn]) -> None: self.__column = converter

        super().__init__()
        
        self.__role: Role = role
        self.__name: str = name
        self.__column: IInitializableConverter[str, ITableColumn] = _ColumnParameterUpdater(self, update) # type: ignore[no-redef]
        self.__cookie: IColumnParameterCookie = ColumnParameterAbstract._ColumnProvider(self)
    
    @final
    def _GetCookie(self) -> IColumnParameterCookie:
        return self.__cookie
    
    @final
    def GetColumnRole(self) -> Role: return self.__role
    @final
    def GetColumnName(self) -> str: return self.__name
    
    @final
    def _SetTableName(self, tableName: str) -> None:
        self.__column.Initialize(tableName)
    
    @final
    def _AsColumn(self, tableName: str) -> ITableColumn:
        return self.__column.Convert(tableName)
class ColumnParameterBase[T: Entity](ColumnParameterAbstract, IColumnParameterBase):
    def __init__(self, func: Converter[T, object], config: IColumnConfigBase) -> None:
        def getName(name: str|None) -> str: return func.__name__ if name is None else name
        
        super().__init__(config.GetRole(), getName(config.GetName()))

class DefaultColumnParameter[TEntity: Entity, TValue, TConfig: IColumnConfigBase](ColumnParameterBase[TEntity], IColumnParameterBase):
    def __init__(self, func: Converter[TEntity, object], config: TConfig) -> None:
        super().__init__(func, config)

        self.__delegate: IColumnParameterDelegate[TValue] = ColumnParameterDelegate[TValue](self._GetCookie())
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode: return self.__delegate.ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode: return self.__delegate.ToConditionNode(operator, value)
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot: return self.__delegate.ToConditionRoot(operator, value)
    
    @final
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter|_ValueNode: return self.__delegate.ToSetConditionParameter(values)
    @final
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode: return self.__delegate.ToSetConditionNode(values)
    @final
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot: return self.__delegate.ToSetConditionRoot(values)

class ColumnParameter[TEntity: Entity, TValue](DefaultColumnParameter[TEntity, TValue, IColumnConfigBase], IColumnParameter[TValue]):
    def __init__(self, func: Converter[TEntity, object], config: IColumnConfigBase) -> None: super().__init__(func, config)
class EntityColumnParameter[TEntity: Entity, TValue: Entity](DefaultColumnParameter[TEntity, TValue, IEntityColumnConfig[TValue]], IEntityColumnParameter[TValue]):
    def __init__(self, func: Converter[TEntity, object], config: IEntityColumnConfig[TValue]) -> None:
        super().__init__(func, config)

        self.__type: Type[TValue] = config.GetType()
    
    @final
    def GetType(self) -> Type[TValue]: return self.__type

class IColumnParameterCookieProvider(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetAt(self, index: int) -> IColumnParameterCookie:
        ...

class ForeignKeyParameter[TEntity: Entity, TValue: Entity](Abstract, IForeignKeyParameter[TValue]):
    @final
    class _CookieProvider[_TEntity: Entity, _TValue: Entity](Abstract, IColumnParameterCookieProvider):
        @final
        class _ColumnProvider[__TEntity: Entity, __TValue: Entity](Abstract, IColumnParameterCookie):
            def __init__(self, parameter: ForeignKeyParameter[__TEntity, __TValue], index: int) -> None:
                super().__init__()

                self.__parameter: ForeignKeyParameter[__TEntity, __TValue] = parameter
                self.__index: int = index
            
            def _AsColumn(self, tableName: str) -> ITableColumn:
                return self.__parameter._AsColumns(tableName).GetAt(self.__index)
        
        def __init__(self, parameter: ForeignKeyParameter[_TEntity, _TValue]) -> None:
            super().__init__()

            self.__parameter: ForeignKeyParameter[_TEntity, _TValue] = parameter
        
        def GetAt(self, index: int) -> IColumnParameterCookie: return ForeignKeyParameter._CookieProvider._ColumnProvider[_TEntity, _TValue](self.__parameter, index)
    
    def __init__(self, name: str, config: IForeignKeyConfig[TValue]) -> None:
        def getNames() -> Iterable[str]:
            columnName: str|None = None

            for column in config.GetNames().AsIterable(): yield column.GetKey().GetValue().GetColumnName() if (columnName := column.GetValue()) is None else columnName

        def update(converter: IInitializableConverter[str, ITuple[ITableColumn]]) -> None: self.__columns = converter
        
        super().__init__()

        self.__name: str = name
        self.__type: Type[TValue] = config.GetType()
        self.__columns: IInitializableConverter[str, ITuple[ITableColumn]] = _ForeignKeyParameterUpdater(getNames(), update) # type: ignore[no-redef]
        self.__delegate: IColumnParameterDelegate[TValue] = ForeignKeyParameterDelegate[TValue](ForeignKeyParameter._CookieProvider[TEntity, TValue](self))
    
    @final
    def GetColumnName(self) -> str: return self.__name
    
    @final
    def GetType(self) -> Type[TValue]: return self.__type
    
    @final
    def _SetTableName(self, tableName: str) -> None:
        self.__columns.Initialize(tableName)
    
    @final
    def _AsColumns(self, tableName: str) -> ITuple[ITableColumn]:
        return self.__columns.Convert(tableName)
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode: return self.__delegate.ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode: return self.__delegate.ToConditionNode(operator, value)
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot: return self.__delegate.ToConditionRoot(operator, value)

class IColumnAbstract(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def IsReadOnly(self) -> bool:
        ...
    
    @abstractmethod
    def GetColumnParameter(self) -> IColumnParameterAbstract:
        ...
    
    @abstractmethod
    def _GetEntityValue(self, obj: Entity) -> object:
        ...
    @abstractmethod
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        ...
class IColumnBase[T: IColumnParameterAbstract](IColumnAbstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetColumnParameter(self) -> T:
        ...

class IDefaultReadOnlyColumnAbstract[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](IReadOnlyPropertyBase[TEntity, TValue, TParameter], IColumnAbstract):
    def __init__(self) -> None: super().__init__()
class IDefaultReadOnlyColumnBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](IDefaultReadOnlyColumnAbstract[TEntity, TValue, TParameter], IReadOnlyProperty[TEntity, TValue, TParameter]):
    def __init__(self) -> None: super().__init__()
class IDefaultColumnBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](IDefaultReadOnlyColumnAbstract[TEntity, TValue, TParameter], IProperty[TEntity, TValue, TParameter]):
    def __init__(self) -> None: super().__init__()

class IDefaultColumn(IColumnBase[IColumnParameterBase]):
    def __init__(self) -> None: super().__init__()
class IDefaultEntityColumn(IColumnBase[IEntityColumnParameterBase]):
    def __init__(self) -> None: super().__init__()

class IReadOnlyColumnBase[TEntity: Entity, TValue](IDefaultReadOnlyColumnAbstract[TEntity, TValue, IColumnParameter[TValue]], IDefaultColumn):
    def __init__(self) -> None: super().__init__()
class IReadOnlyColumn[TEntity: Entity, TValue](IReadOnlyColumnBase[TEntity, TValue], IDefaultReadOnlyColumnBase[TEntity, TValue, IColumnParameter[TValue]], IDefaultColumn):
    def __init__(self) -> None: super().__init__()
class IColumn[TEntity: Entity, TValue](IReadOnlyColumnBase[TEntity, TValue], IDefaultColumnBase[TEntity, TValue, IColumnParameter[TValue]]):
    def __init__(self) -> None: super().__init__()

class _IAutoPrimaryKey[TEntity: Entity, TValue](IReadOnlyColumn[TEntity, TValue]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _SetGeneratedValue(self, obj: Entity, value: object) -> None:
        ...

class IEntityColumn[TEntity: Entity, TValue: Entity](IDefaultColumnBase[TEntity, TValue, IEntityColumnParameter[TValue]], IDefaultEntityColumn):
    def __init__(self) -> None: super().__init__()

class IDefaultForeignKey(IColumnBase[IForeignKeyParameterBase]):
    def __init__(self) -> None: super().__init__()
class IForeignKey[TEntity: Entity, TValue: Entity](IDefaultColumnBase[TEntity, TValue, IForeignKeyParameter[TValue]], IDefaultForeignKey):
    def __init__(self) -> None: super().__init__()

class _ColumnConfigDecoratorBase[TConfig: IColumnConfigBase](Abstract):
    def __init__(self, config: TConfig) -> None:
        super().__init__()

        self.__config: TConfig = config
    
    @final
    def _GetConfig(self) -> TConfig:
        return self.__config
    
    @abstractmethod
    def __call__[TEntity: Entity, TValue](self, func: Property[TEntity, TValue]) -> IReadOnlyColumnBase[TEntity, TValue]:
        ...
@final
class _ColumnConfigDecorator(_ColumnConfigDecoratorBase[IColumnConfig]):
    def __init__(self, config: IColumnConfig) -> None:
        super().__init__(config)
    
    def __call__[TEntity: Entity, TValue](self, func: Property[TEntity, TValue]) -> IColumn[TEntity, TValue]:
        return _Column[TEntity, TValue](func, self._GetConfig())

class _ReadOnlyColumnConfigDecoratorBase[TConfig: IColumnConfigBase](Abstract):
    def __init__(self, config: TConfig) -> None:
        super().__init__()

        self.__config: TConfig = config
    
    @final
    def _GetConfig(self) -> TConfig:
        return self.__config
    
    @abstractmethod
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumnBase[TEntity, TValue]:
        ...

@final
class _ReadOnlyColumnConfigDecorator(_ReadOnlyColumnConfigDecoratorBase[IColumnConfig]):
    def __init__(self, config: IColumnConfig) -> None: super().__init__(config)
    
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        return _ReadOnlyColumn[TEntity, TValue](func, self._GetConfig())

@final
class _PrimaryKeyConfigDecorator(_ReadOnlyColumnConfigDecoratorBase[IPrimaryKeyConfig]):
    def __init__(self, config: IPrimaryKeyConfig) -> None: super().__init__(config)
    
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        return _PrimaryKey[TEntity, TValue](func, self._GetConfig())
@final
class _AutoPrimaryKeyConfigDecorator(_ColumnConfigDecoratorBase[IPrimaryKeyConfig]):
    def __init__(self, config: IPrimaryKeyConfig) -> None:
        super().__init__(config)

    def __call__[TEntity: Entity, TValue](self, func: Property[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        return _AutoPrimaryKey[TEntity, TValue](func, self._GetConfig())

class _EntityColumnConfigDecoratorBase[TValue: Entity, TConfig, TColumn](Abstract):
    def __init__(self, config: TConfig) -> None:
        super().__init__()

        self.__config: TConfig = config
    
    @final
    def _GetConfig(self) -> TConfig:
        return self.__config
    
    @abstractmethod
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> TColumn:
        ...

@final
class _EntityColumnConfigDecorator[TValue: Entity](_EntityColumnConfigDecoratorBase[TValue, IEntityColumnConfig[TValue], IDefaultEntityColumn]):
    def __init__(self, config: IEntityColumnConfig[TValue]) -> None: super().__init__(config)
    
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> IEntityColumn[TEntity, TValue]:
        return _EntityColumn[TEntity, TValue](func, self._GetConfig())
@final
class _ForeignKeyConfigDecorator[TValue: Entity](_EntityColumnConfigDecoratorBase[TValue, IForeignKeyConfig[TValue], IDefaultForeignKey]):
    def __init__(self, config: IForeignKeyConfig[TValue]) -> None: super().__init__(config)
    
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> IForeignKey[TEntity, TValue]:
        return _ForeignKey[TEntity, TValue](func, self._GetConfig())

def readOnlyColumnConfig(name: str|None = None) -> _ReadOnlyColumnConfigDecorator:
    return _ReadOnlyColumnConfigDecorator(ColumnConfig(name))
def columnConfig(name: str|None = None) -> _ColumnConfigDecorator:
    return _ColumnConfigDecorator(ColumnConfig(name))

def primaryKeyConfig(name: str|None = None) -> _PrimaryKeyConfigDecorator:
    return _PrimaryKeyConfigDecorator(PrimaryKeyConfig(name))
def autoPrimaryKeyConfig(name: str | None = None) -> _AutoPrimaryKeyConfigDecorator:
    return _AutoPrimaryKeyConfigDecorator(PrimaryKeyConfig(name))

def entityColumnConfig[T: Entity](t: Type[T], name: str|None = None) -> _EntityColumnConfigDecorator[T]:
    return _EntityColumnConfigDecorator[T](EntityColumnConfig[T](t, name))

def foreignKeyConfiguration[T: Entity](t: Type[T], columns: IReadOnlyDictionary[IParameterKey, str|None]) -> _ForeignKeyConfigDecorator[T]:
    return _ForeignKeyConfigDecorator[T](ForeignKeyConfig[T](t, columns))
def foreignKeyConfig[T: Entity](t: Type[T], columns: Iterable[tuple[IColumnParameterAbstract, str|None]]) -> _ForeignKeyConfigDecorator[T]:
    return foreignKeyConfiguration(t, CreateDictionary(dict[IParameterKey, str|None](Select(columns, lambda column: (ParameterKey(column[0]), column[1])))).AsReadOnly())

class CookieOrigin(Enum):
    Null = 0
    Application = 1
    DataBase = 2

class ICookie(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetOrigin(self) -> CookieOrigin:
        ...
    
    @abstractmethod
    def IsReady(self) -> bool:
        ...
    
    @abstractmethod
    def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T:
        ...
    @abstractmethod
    def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None:
        ...

    @abstractmethod
    def GetDirtyColumns(self) -> IReadOnlySet[IString]:
        ...

    @abstractmethod
    def _CommitChanges(self) -> None:
        ...
    @abstractmethod
    def _RevertChanges(self) -> None:
        ...

def _GetCookie(obj: Entity) -> ICookie:
    return obj._GetCookie() # pyright: ignore[reportPrivateUsage]

def _TryGetEntityContext(obj: Entity) -> DataContextBase|None:
    return obj._TryGetContext() # pyright: ignore[reportPrivateUsage]
def _SetEntityContext(obj: Entity, context: DataContextBase) -> ICookie:
    return obj._SetContext(context) # pyright: ignore[reportPrivateUsage]

class _ColumnDecoratorBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract, TProperty](Abstract, IFunctionProvider[TEntity, TValue, TProperty]):
    def __init__(self, parameter: TParameter, func: TProperty, setter: SetterBase[Entity, object]) -> None:
        super().__init__()
        
        _func: GetterBase[TEntity, TValue] = self._AsFunction(func)

        self.__parameter: TParameter = parameter
        self.__getter: GetterBase[Entity, object] = lambda entity: _func(cast(TEntity, entity))
        self.__setter: SetterBase[Entity, object] = setter
    
    @final
    def GetColumnParameter(self) -> TParameter: return self.__parameter
    
    @final
    def GetEntityValue(self, obj: Entity, name: str) -> object: return _GetCookie(obj).GetValue(name, self.__getter)
    @final
    def GetValue(self, obj: TEntity|None, name: str) -> TValue|TParameter: return self.GetColumnParameter() if obj is None else cast(TValue, _GetCookie(obj).GetValue(name, self.__getter))
    
    def SetValue(self, obj: Entity, name: str, value: object) -> None: _GetCookie(obj).SetValue(name, self.__setter, value)

@final
class _ReadOnlyColumnDecorator[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](_ColumnDecoratorBase[TEntity, TValue, TParameter, GetterBase[TEntity, TValue]], IGetterProvider[TEntity, TValue]):
    def __init__(self, parameter: TParameter, func: GetterBase[TEntity, TValue]) -> None:
        def setValue(entity: Entity) -> IMethodBase[object]: raise InvalidOperationError("Cannot update read-only column or primary key.")

        super().__init__(parameter, func, setValue)
@final
class _ColumnDecorator[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](_ColumnDecoratorBase[TEntity, TValue, TParameter, Property[TEntity, TValue]], IPropertyProvider[TEntity, TValue]):
    def __init__(self, parameter: TParameter, func: Property[TEntity, TValue]) -> None: super().__init__(parameter, func, lambda entity: cast(IMethodBase[object], func(cast(TEntity, entity)).AsMethod()))
    
def _GetName[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](column: _IReadOnlyColumnBase[TEntity, TValue, TDecorator, TConfig, TParameter, TProperty]) -> str:
    return column._GetDecoratorAsInterface().GetColumnParameter().GetColumnName() # pyright: ignore[reportPrivateUsage]

class _IReadOnlyColumnBase[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](IReadOnlyPropertyBase[TEntity, TValue, TParameter], IColumnAbstract):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _AsDecorator(self, decorator: TDecorator) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, TProperty]:
        ...
    
    @abstractmethod
    def _GetDecorator(self) -> TDecorator:
        ...
    @final
    def _GetDecoratorAsInterface(self) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, TProperty]:
        return self._AsDecorator(self._GetDecorator())
    
    @final
    def GetColumnParameter(self) -> TParameter: return self._GetDecoratorAsInterface().GetColumnParameter()
    
    @final
    def _GetValue(self, obj: TEntity|None) -> TValue|TParameter:
        return self._GetDecoratorAsInterface().GetValue(obj, _GetName(self))
    @final
    def _GetEntityValue(self, obj: Entity) -> object: return self._GetDecoratorAsInterface().GetEntityValue(obj, _GetName(self))

class _IReadOnlyColumn[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](IReadOnlyProperty[TEntity, TValue, TParameter], _IReadOnlyColumnBase[TEntity, TValue, TDecorator, TConfig, TParameter, TProperty]):
    def __init__(self) -> None: super().__init__()
class _IColumn[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](IProperty[TEntity, TValue, TParameter], _IReadOnlyColumnBase[TEntity, TValue, TDecorator, TConfig, TParameter, TProperty]):
    def __init__(self) -> None: super().__init__()

class _ReadOnlyColumnAbstract[TEntity: Entity, TValue, TConfig: IColumnConfigBase, TProperty](ReadOnlyPropertyDecoratorBase[TEntity, TValue, IColumnParameter[TValue], TProperty], _IReadOnlyColumn[TEntity, TValue, _ReadOnlyColumnDecorator[TEntity, TValue, IColumnParameter[TValue]], TConfig, IColumnParameter[TValue], GetterBase[TEntity, TValue]]):
    def __init__(self, func: TProperty, config: TConfig) -> None:
        super().__init__(func)

        _func: GetterBase[TEntity, TValue] = self._AsFunction(func)

        self.__decorator: _ReadOnlyColumnDecorator[TEntity, TValue, IColumnParameter[TValue]] = _ReadOnlyColumnDecorator[TEntity, TValue, IColumnParameter[TValue]](ColumnParameter[TEntity, TValue](_func, config), _func)
    
    @final
    def _AsDecorator(self, decorator: _ReadOnlyColumnDecorator[TEntity, TValue, IColumnParameter[TValue]]) -> _ColumnDecoratorBase[TEntity, TValue, IColumnParameter[TValue], GetterBase[TEntity, TValue]]: return decorator
    
    @final
    def _GetDecorator(self) -> _ReadOnlyColumnDecorator[TEntity, TValue, IColumnParameter[TValue]]: return self.__decorator
    
    @final
    def IsReadOnly(self) -> bool: return True
    
    @final
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|IColumnParameter[TValue]: return self._GetValue(obj)
    
    @final
    def _SetEntityValue(self, obj: Entity, value: object) -> None: self._GetDecorator().SetValue(obj, _GetName(self), value)

class _ReadOnlyColumnBase[TEntity: Entity, TValue, TConfig: IColumnConfigBase](_ReadOnlyColumnAbstract[TEntity, TValue, TConfig, GetterBase[TEntity, TValue]], IGetterProvider[TEntity, TValue]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: TConfig) -> None:
        super().__init__(func, config)
class _AutoPrimaryKeyBase[TEntity: Entity, TValue, TConfig: IColumnConfigBase](_ReadOnlyColumnAbstract[TEntity, TValue, TConfig, Property[TEntity, TValue]], IPropertyProvider[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: TConfig) -> None:
        super().__init__(func, config)

class _ColumnAbstract[TEntity: Entity, TValue, TParameter](PropertyDecorator[TEntity, TValue, TParameter]):
    def __init__(self, func: Property[TEntity, TValue]) -> None: super().__init__(func)
    
    @final
    def IsReadOnly(self) -> bool: return False

class _ColumnBase[TEntity: Entity, TValue, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase](_ColumnAbstract[TEntity, TValue, TParameter], _IColumn[TEntity, TValue, _ColumnDecorator[TEntity, TValue, TParameter], TConfig, TParameter, Property[TEntity, TValue]]):
    def __init__(self, func: Property[TEntity, TValue], config: TConfig) -> None:
        super().__init__(func)

        self.__decorator: _ColumnDecorator[TEntity, TValue, TParameter] = _ColumnDecorator[TEntity, TValue, TParameter](self._CreateParameter(func, config), self._GetFunc())
    
    @abstractmethod
    def _CreateParameter(self, func: Property[TEntity, TValue], config: TConfig) -> TParameter:
        ...
    
    @final
    def _AsDecorator(self, decorator: _ColumnDecorator[TEntity, TValue, TParameter]) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, Property[TEntity, TValue]]: return decorator
    
    @final
    def _GetDecorator(self) -> _ColumnDecorator[TEntity, TValue, TParameter]: return self.__decorator
    
    @final
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|TParameter: return self._GetValue(obj)
    
    @final
    def Set(self, obj: TEntity, value: TValue, objtype: type|None = None) -> None: self._GetDecorator().SetValue(obj, _GetName(self), value)
    @final
    def _SetEntityValue(self, obj: Entity, value: object) -> None: self._GetDecorator().SetValue(obj, _GetName(self), value)

@final
class _ReadOnlyColumn[TEntity: Entity, TValue](_ReadOnlyColumnBase[TEntity, TValue, IColumnConfig], IReadOnlyColumn[TEntity, TValue]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: IColumnConfig) -> None: super().__init__(func, config)
@final
class _Column[TEntity: Entity, TValue](_ColumnBase[TEntity, TValue, IColumnConfig, IColumnParameter[TValue]], IColumn[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IColumnConfig) -> None: super().__init__(func, config)
    
    def _CreateParameter(self, func: Property[TEntity, TValue], config: IColumnConfig) -> IColumnParameter[TValue]: return ColumnParameter[TEntity, TValue](func, config)

@final
class _PrimaryKey[TEntity: Entity, TValue](_ReadOnlyColumnBase[TEntity, TValue, IPrimaryKeyConfig], IReadOnlyColumn[TEntity, TValue]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: IPrimaryKeyConfig) -> None: super().__init__(func, config)
@final
class _AutoPrimaryKey[TEntity: Entity, TValue](_AutoPrimaryKeyBase[TEntity, TValue, IPrimaryKeyConfig], _IAutoPrimaryKey[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IPrimaryKeyConfig) -> None:
        super().__init__(func, config)

    @final
    def _SetGeneratedValue(self, obj: Entity, value: object) -> None:
        self._GetFunc()(cast(TEntity, obj)).SetValue(cast(TValue, value))

@final
class _EntityColumn[TEntity: Entity, TValue: Entity](_ColumnBase[TEntity, TValue, IEntityColumnConfig[TValue], IEntityColumnParameter[TValue]], IEntityColumn[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IEntityColumnConfig[TValue]) -> None: super().__init__(func, config)
    
    def _CreateParameter(self, func: Property[TEntity, TValue], config: IEntityColumnConfig[TValue]) -> IEntityColumnParameter[TValue]: return EntityColumnParameter[TEntity, TValue](func, config)

@final
class _ForeignKey[TEntity: Entity, TValue: Entity](_ColumnAbstract[TEntity, TValue, IForeignKeyParameter[TValue]], IForeignKey[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IForeignKeyConfig[TValue]) -> None:
        super().__init__(func)

        self.__decorator: _ColumnDecorator[TEntity, TValue, IForeignKeyParameter[TValue]] = _ColumnDecorator[TEntity, TValue, IForeignKeyParameter[TValue]](ForeignKeyParameter[TEntity, TValue](func.__name__, config), func)
    
    def __GetName(self) -> str:
        return self.__decorator.GetColumnParameter().GetColumnName()
    
    def GetColumnParameter(self) -> IForeignKeyParameter[TValue]: return self.__decorator.GetColumnParameter()
    
    def _GetEntityValue(self, obj: Entity) -> object: return self.__decorator.GetEntityValue(obj, self.__GetName())
    def _SetEntityValue(self, obj: Entity, value: object) -> None: self.__decorator.SetValue(obj, self.__GetName(), value)
    
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|IForeignKeyParameter[TValue]: return self.__decorator.GetValue(obj, self.__GetName())
    def Set(self, obj: TEntity, value: TValue) -> None: self.__decorator.SetValue(obj, self.__GetName(), value)

def tableConfig(name: str) -> Selector[Type[Entity]]:
    def decorator(cls: Type[Entity]) -> Type[Entity]:
        def getColumns() -> Generator[IColumnAbstract]:
            for member in cls.__dict__.values():
                if isinstance(member, IColumnAbstract):
                    member.GetColumnParameter()._SetTableName(name) # pyright: ignore[reportPrivateUsage]
                    
                    yield member
        
        cls.__columns = ValueFunction[_Columns](_Columns(getColumns())) # pyright: ignore[reportPrivateUsage]

        return cls
    
    return decorator

@final
class _Columns(Abstract):
    def __init__(self, columns: Iterable[IColumnAbstract]) -> None:
        def checkRole(column: IColumnAbstract, role: Role) -> bool: return column.GetColumnParameter().GetColumnRole() == role
        def getPredicate(role: Role) -> Predicate[IColumnAbstract]: return lambda column: checkRole(column, role)
        def concatenate(*columns: IEnumerable[IColumnAbstract]) -> Iterator[IColumnAbstract]: return ConcatenateIterables(Select(columns, lambda items: items.AsIterable()))
        
        super().__init__()

        # Classify each column NON-destructively by (type, role) over the materialized, re-iterable
        # list; iterating the whole list per bucket preserves declaration order (mandatory: composite-PK
        # order drives the identity key and the UPDATE/DELETE WHERE). The four buckets are disjoint.
        # IDefaultColumn matches plain columns and primary keys only; entity columns and foreign keys are
        # sibling types (distinct runtime classes), so they are picked by their own WhereOfType.
        allColumns: ITuple[IColumnAbstract] = CreateTuple(columns)

        self.__primaryKeys: ITuple[IDefaultColumn] = CreateTuple(Include(WhereOfType(IDefaultColumn, allColumns.AsIterable()), getPredicate(Role.PrimaryKey))) # type: ignore[type-abstract]
        self.__foreignKeys: ITuple[IDefaultForeignKey] = CreateTuple(WhereOfType(IDefaultForeignKey, allColumns.AsIterable())) # type: ignore[type-abstract]
        self.__entityColumns: ITuple[IDefaultEntityColumn] = CreateTuple(Include(WhereOfType(IDefaultEntityColumn, allColumns.AsIterable()), getPredicate(Role.ForeignKey))) # type: ignore[type-abstract]
        self.__columns: ITuple[IDefaultColumn] = CreateTuple(Exclude(WhereOfType(IDefaultColumn, allColumns.AsIterable()), getPredicate(Role.PrimaryKey))) # type: ignore[type-abstract]

        self.__allColumns: Iterable[IColumnAbstract] = CreateIteratorProvider(lambda: concatenate(self.__primaryKeys, self.__columns, self.__entityColumns, self.__foreignKeys))
    
    def GetPrimaryKeys(self) -> ITuple[IDefaultColumn]:
        return self.__primaryKeys
    def GetColumns(self) -> ITuple[IDefaultColumn]:
        return self.__columns
    def GetEntityColumns(self) -> ITuple[IDefaultEntityColumn]:
        return self.__entityColumns
    def GetForeignKeys(self) -> ITuple[IDefaultForeignKey]:
        return self.__foreignKeys
    
    def GetAllColumns(self) -> Iterable[IColumnAbstract]:
        return self.__allColumns

@final
class _EntityUpdater(ValueFunctionUpdater[_Columns]):
    def __init__(self, t: Type[Entity], updater: Method[IFunction[_Columns]]) -> None:
        super().__init__(updater)

        self.__type: Type[Entity] = t
    
    @final
    def _GetValue(self) -> _Columns: return _Columns(WhereOfType(IColumnAbstract, self.__type.__dict__.values())) # type: ignore[type-abstract]

class IEntityKey[T: IItem](IItemObject[T, 'IEntityKey[T]|T'], IEnumerable[IValueItem]):
    def __init__(self) -> None: super().__init__()

class EntityKeyBase[T: IItem](Abstract, IEntityKey[T]):
    def __init__(self, key: T, enumerable: IEnumerable[IValueItem]) -> None:
        super().__init__()

        self.__key: T = key
        self.__enumerable: IEnumerable[IValueItem] = enumerable
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IValueItem]|None: return self.__enumerable.TryGetEnumerator()
    
    @final
    def AsIterable(self) -> Iterable[IValueItem]: return self.__enumerable.AsIterable()
    
    @final
    def GetValue(self) -> T: return self.__key
    @final
    def GetUnderlyingValue(self) -> T: return self.GetValue()
    
    def Equals(self, item: T|IEntityKey[T]|object) -> bool: return self.GetValue().Equals(item.GetUnderlyingValue() if isinstance(item, IEntityKey) else item)
    def Hash(self) -> int: return self.GetValue().Hash()
    
    def ToString(self) -> str: return self.GetValue().ToString()
class EntityKey[T: IValueItem](EntityKeyBase[T], IEntityKey[T]):
    @final
    class _Enumerable[_T: IValueItem](Enumerable[_T]):
        @final
        class _Enumerator[__T: IValueItem](EnumeratorBase[__T]):
            def __init__(self, key: IEntityKey[__T]) -> None:
                super().__init__()

                self.__key: IEntityKey[__T] = key
                self.__canMoveNext: bool|None = True
            
            def IsResetSupported(self) -> bool: return True
            
            def _GetCurrent(self) -> __T:
                if self.__canMoveNext is None: return self.__key.GetValue()
                
                raise GetEnumeratorInactiveError()
            
            def _MoveNextOverride(self) -> bool:
                canMoveNext: bool|None = self.__canMoveNext

                if canMoveNext is True:
                    self.__canMoveNext = None

                    return True
                
                if canMoveNext is None: self.__canMoveNext = False

                return False
            
            def _ResetOverride(self) -> bool:
                self.__canMoveNext = True
                
                return True
            
            def _OnStopped(self) -> None:
                pass
        
        def __init__(self, key: EntityKey[_T]) -> None:
            super().__init__()

            self.__key: IEntityKey[_T] = key
        
        def TryGetEnumerator(self) -> IEnumerator[_T]|None: return EntityKey[_T]._Enumerable._Enumerator(self.__key)
    
    def __init__(self, key: T) -> None: super().__init__(key, EntityKey[T]._Enumerable(self))
class CompositeEntityKey[T: IValueItem](EntityKeyBase[IHashableTuple[T]], IEntityKey[IHashableTuple[T]]):
    # keys is both the underlying value and the enumerable (an IHashableTuple is an IEnumerable of its
    # items). Passing self.GetValue() here read __key before EntityKeyBase.__init__ had set it.
    def __init__(self, keys: IHashableTuple[T]) -> None: super().__init__(keys, keys)

    # Value equality/hash over the primary-key items (each an IValueItem with value semantics, like the
    # single-column EntityKey). The inherited EntityKeyBase behaviour delegates to the underlying
    # IHashableTuple, whose Equals is identity-based (self is item) -> two logically equal composite
    # keys never match and the identity map misses. This override keeps that scoped to the ORM key.
    @final
    def Equals(self, item: object) -> bool:
        if not isinstance(item, IEntityKey): return False

        selfItems: list[IValueItem] = list(self.AsIterable())
        otherItems: list[IValueItem] = list(item.AsIterable())

        return len(selfItems) == len(otherItems) and all(a.Equals(b) for a, b in zip(selfItems, otherItems))
    @final
    def Hash(self) -> int: return hash(tuple(item.Hash() for item in self.AsIterable()))

def _GetEntityValue(obj: Entity, column: IColumnAbstract) -> object:
    return column._GetEntityValue(obj) # pyright: ignore[reportPrivateUsage]
def _SetEntityValue(obj: Entity, column: IColumnAbstract, value: object) -> None:
    column._SetEntityValue(obj, value) # pyright: ignore[reportPrivateUsage]

def _ProcessColumnsCore[TColumn: IColumnAbstract](obj: Entity, columns: Iterable[TColumn], row: Iterable[object], converter: Converter[tuple[TColumn, object], object]) -> None:
    def setValue(args: tuple[TColumn, object]) -> None: _SetEntityValue(obj, args[0], converter(args))

    DoForEach(zip(columns, row), setValue)
def _ProcessColumns[TColumn: IColumnAbstract](obj: Entity, row: Iterable[object], columns: Iterable[TColumn]) -> None:
    _ProcessColumnsCore(obj, columns, row, lambda args: args[1])

def _EnsureNoUnresolvedRollbackError(context: DataContextBase) -> None:
    if context.IsBlocked(): raise UnresolvedRollbackError()

class IEntityMapperBase[T: Entity](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsKey(self) -> IType[T]:
        ...

    @abstractmethod
    def GetKey(self, keys: ITuple[object]) -> IEntityKey[IItem]:
        ...
    
    @abstractmethod
    def TryGetEntity(self, key: IEntityKey[IItem]) -> T|None:
        ...
    
    @abstractmethod
    def GetOrCreateEntity(self, key: IEntityKey[IItem]) -> T:
        ...
    @final
    def GetOrCreateEntityFromKeys(self, keys: ITuple[object]) -> T:
        return self.GetOrCreateEntity(self.GetKey(keys))
class IEntityMapper[T: Entity](IEntityMapperBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Register(self, key: IEntityKey[IItem], entity: T) -> None:
        ...
    @abstractmethod
    def Unregister(self, key: IEntityKey[IItem]) -> None: 
        ...
class EntityMapper[T: Entity](Abstract, IEntityMapper[T]):
    def __init__(self, t: Type[T], context: DataContextBase) -> None:
        super().__init__()

        self.__type: IType[T] = TypeObject[T](t)
        self.__items: IDictionary[IEntityKey[IItem], T] = Dictionary[IEntityKey[IItem], T]()
        self.__context: DataContextBase = context
    
    @final
    def _GetItems(self) -> IDictionary[IEntityKey[IItem], T]:
        return self.__items
    
    @final
    def AsKey(self) -> IType[T]: return self.__type

    @final
    def GetKey(self, keys: ITuple[object]) -> IEntityKey[IItem]:
        def getKey(key: object) -> IValueItem: return Map(key)
        
        t: Type[T] = self.__type.GetValue()
        count: int = _GetPrimaryKeys(t).GetCount()

        if keys.GetCount() == count:
            if count < 1: raise InvalidOperationError("No primary key found.")
            
            return CompositeEntityKey[IValueItem](CreateHashableTuple(Select(keys.AsIterable(), getKey))) if count > 1 else EntityKey[IValueItem](getKey(keys.GetAt(0)))

        raise ValueError(f"The given key collection's length does not match the primary keys length of {t}.")
    
    @final
    def TryGetEntity(self, key: IEntityKey[IItem]) -> T|None: return self._GetItems().TryGetValue(key).TryGetValue()
    
    @final
    def GetOrCreateEntity(self, key: IEntityKey[IItem]) -> T:
        entity: T|None = self.TryGetEntity(key)
        
        if entity is None:
            t: Type[T] = self.AsKey().GetValue()
            
            self._GetItems().Add(key, entity := object.__new__(t))
            
            entity._InitCookie() # pyright: ignore[reportPrivateUsage]
            
            _SetEntityContext(entity, self.__context)
            
            _ProcessColumns(entity, Select(key.AsIterable(), lambda key: key.GetValue()), _GetPrimaryKeys(t).AsIterable())
        
        return entity
    
    @final
    def Register(self, key: IEntityKey[IItem], entity: T) -> None: self._GetItems().Add(key, entity)
    @final
    def Unregister(self, key: IEntityKey[IItem]) -> None: self._GetItems().Remove(key)

class Entity(Abstract, IDisposable):
    class _Cookie(Abstract, ICookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__()

            self.__entity: Entity = entity
            self.__context: DataContextBase|None = None # This field is declared here to ensure the reference exists, no matter which initialization path is used.
            self.__isDeleted: IMonitor = Monitor() # Tombstone flag; declared here so the reference exists on both initialization paths, like __context.
        
        @final
        def _GetEntity(self) -> Entity:
            return self.__entity
        
        @final
        def _TryGetContext(self) -> DataContextBase|None:
            return self.__context
        @final
        def _SetContext(self, context: DataContextBase) -> None:
            self.__context = context
        
        @final
        def _IsDeleted(self) -> bool:
            return self.__isDeleted.IsBusy()
        @final
        def _MarkDeleted(self) -> None:
            self.__isDeleted.Initialize()
        @final
        def _UnmarkDeleted(self) -> None:
            self.__isDeleted.Dispose()
        
        @abstractmethod
        def Seal(self) -> None:
            ...
    
    @final
    class _AppCookie(_Cookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__(entity)

            self.__original: IDictionary[IString, Any]|None = None
        
        def GetOrigin(self) -> CookieOrigin: return CookieOrigin.Application
        
        def IsReady(self) -> bool: return True
        
        def Seal(self) -> None: pass
        
        def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T: return func(self._GetEntity()).GetValue()
        def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None: return func(self._GetEntity()).SetValue(value)
        
        def __GetTrackedColumns(self) -> Iterable[IColumnAbstract]:
            # Recompare scope: writable columns (settable after construction) + primary keys.
            # Primary keys are tracked to detect a primary-key mutation performed by bypassing
            # the read-only setter (direct struct reassignment); see the PK-drift guard.
            return Exclude(
                _GetColumns(self._GetEntity()).GetAllColumns(),
                lambda column: column.IsReadOnly() and column.GetColumnParameter().GetColumnRole() != Role.PrimaryKey)
        
        def __Snapshot(self) -> IDictionary[IString, Any]:
            entity: Entity = self._GetEntity()
            snapshot: IDictionary[IString, Any] = Dictionary[IString, Any]()

            for column in self.__GetTrackedColumns(): snapshot.AddOrUpdate(String(column.GetColumnParameter().GetColumnName()), _GetEntityValue(entity, column))

            return snapshot
        
        def GetDirtyColumns(self) -> IReadOnlySet[IString]:
            original: IDictionary[IString, Any]|None = self.__original

            if original is None: raise InvalidOperationError("The entity is not attached; its baseline has not been established.")

            entity: Entity = self._GetEntity()
            
            return CreateSet(Match(self.__GetTrackedColumns(), lambda column: String(column.GetColumnParameter().GetColumnName()), lambda column, name: _GetEntityValue(entity, column) != original.TryGetValue(name).GetValue()))
        
        def _CommitChanges(self) -> None:
            self.__original = self.__Snapshot()
        def _RevertChanges(self) -> None:
            original: IDictionary[IString, Any]|None = self.__original

            if original is None: return

            entity: Entity = self._GetEntity()

            # Rewrite the baseline into the writable structs. Primary keys are intentionally left
            # out: they are read-only (their setter raises), and a drifted PK is an error state
            # resolved by dooming the transaction, not by silent restoration.
            for column in Exclude(_GetColumns(entity).GetAllColumns(), lambda column: column.IsReadOnly()):
                _SetEntityValue(entity, column, original.TryGetValue(String(column.GetColumnParameter().GetColumnName())).GetValue())
    @final
    class _DBCookie(_Cookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__(entity)

            self.__isReady: bool = False
            self.__values: IDictionary[IString, Any] = Dictionary[IString, Any]()
            self.__dirty: IDictionary[IString, Any] = Dictionary[IString, Any]()

        def GetOrigin(self) -> CookieOrigin:
            return CookieOrigin.DataBase

        def IsReady(self) -> bool: return self.__isReady

        def Seal(self) -> None: self.__isReady = True

        def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T:
            key: IString = String(name)

            return cast(T, (self.__dirty if self.__dirty.ContainsKey(key) else self.__values).TryGetValue(key).GetValue())
        def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None:
            # Pre-seal writes (hydration / identity set) establish the pristine row in __values;
            # post-seal consumer mutations are recorded in the __dirty overlay.
            (self.__dirty if self.__isReady else self.__values).AddOrUpdate(String(name), value)

        def GetDirtyColumns(self) -> IReadOnlySet[IString]:
            return CreateSet(self.__dirty.GetKeys().AsIterable())

        def _CommitChanges(self) -> None:
            for key in self.__dirty.GetKeys().AsIterable(): self.__values.AddOrUpdate(key, self.__dirty.TryGetValue(key).GetValue())

            self.__dirty.Clear()
        def _RevertChanges(self) -> None:
            self.__dirty.Clear()
    
    __columns: IFunction[_Columns]
    
    def __init_subclass__(cls, **kwargs: object) -> None:
        def update(func: IFunction[_Columns]) -> None: cls.__columns = func
        
        super().__init_subclass__(**kwargs)
        
        cls.__columns = _EntityUpdater(cls, update)
    
    def __init__(self) -> None:
        super().__init__()
        
        self.__cookie: Entity._Cookie = Entity._AppCookie(self)
    
    @classmethod
    @final
    def _GetColumns(cls) -> _Columns:
        return cls.__columns.GetValue()
    
    @final
    def _InitCookie(self) -> None:
        self.__cookie = Entity._DBCookie(self)
    
    @final
    def _GetCookie(self) -> ICookie:
        return self.__cookie
    
    @final
    def _TryGetContext(self) -> DataContextBase|None:
        return self.__cookie._TryGetContext() # pyright: ignore[reportPrivateUsage]
    @final
    def _SetContext(self, context: DataContextBase) -> ICookie:
        cookie: Entity._Cookie = self.__cookie

        cookie._SetContext(context) # pyright: ignore[reportPrivateUsage]

        return cookie
    
    @final
    def _IsDeleted(self) -> bool:
        return self.__cookie._IsDeleted() # pyright: ignore[reportPrivateUsage]
    @final
    def _MarkDeleted(self) -> None:
        self.__cookie._MarkDeleted() # pyright: ignore[reportPrivateUsage]
    @final
    def _UnmarkDeleted(self) -> None:
        self.__cookie._UnmarkDeleted() # pyright: ignore[reportPrivateUsage]
    
    @final
    def IsReady(self) -> bool:
        return self._GetCookie().IsReady()
    
    @final
    def TryUpdate(self) -> bool:
        context: DataContextBase|None = self._TryGetContext()
        
        if context is None: raise EntityNotPersistedError(self)
        
        _EnsureNoUnresolvedRollbackError(context)
        
        transaction: ITransaction|None = context.TryGetActiveTransaction()
        
        if transaction is None: raise InvalidOperationError("UPDATE requires an active transaction.")
        
        return transaction.TryUpdate(self)
    
    @final
    def Delete(self) -> None:
        # Ordered checks (C2). Uses the context handle (_TryGetContext), not _IsInstancePersisted:
        # a DB-origin entity is deletable but absent from __persisted. Mirror of TryUpdate.

        if self._IsDeleted(): raise DeletedEntityError(self)             # 1. tombstone terminal (handle kept -> context alone can't tell)
        
        context: DataContextBase|None = self._TryGetContext()
        
        if context is None: raise EntityNotPersistedError(self)          # 2. not attached (transient, or inserted-not-promoted)
        
        _EnsureNoUnresolvedRollbackError(context)                        # 3. inherited block gate (C1: DELETE respects it, never arms it)
        
        transaction: ITransaction|None = context.TryGetActiveTransaction()
        
        if transaction is None: raise InvalidOperationError("DELETE requires an active transaction.") # 4.
        
        transaction.Delete(self)

    @final
    def _Initialize(self) -> None:
        self.__cookie.Seal()
    
    def Dispose(self) -> None:
        pass

@final
class _SelectionQueryData(Abstract):
    def __init__(self, columns: _Columns) -> None:
        super().__init__()

        self.__columns: _Columns = columns
    
    def GetPrimaryKeys(self) -> Iterable[IDefaultColumn]:
        return self.__columns.GetPrimaryKeys().AsIterable()
    def GetColumns(self) -> Iterable[IDefaultColumn]:
        return self.__columns.GetColumns().AsIterable()
    def GetEntityColumns(self) -> Iterable[IDefaultEntityColumn]:
        return self.__columns.GetEntityColumns().AsIterable()
    def GetForeignKeys(self) -> Iterable[IDefaultForeignKey]:
        return self.__columns.GetForeignKeys().AsIterable()
    
    def GetAllColumns(self) -> Iterable[IColumnAbstract]:
        return self.__columns.GetAllColumns()

def _GetTable(context: DataContextBase, t: Type[Entity]|Entity) -> ITable:
    table: ITable|None = context._GetConnection().GetCursor().TryGetTable(GetTypeName(t)) # pyright: ignore[reportPrivateUsage]

    if table is None: raise ValueError("Unknown table.")

    return table

@final
class _Hydrator[T: Entity](Abstract):
    def __init__(self, t: Type[T], context: DataContextBase) -> None:
        super().__init__()
        
        self.__type: Type[T] = t
        self.__context: DataContextBase = context
        self.__data: _SelectionQueryData = _SelectionQueryData(_GetColumns(t))

    def GetDefaultTableName(self) -> str:
        return GetTypeName(self.__type)

    def GetSelectionColumnSet(self) -> IColumnParameterSet[IFormattable]:
        data: _SelectionQueryData = self.__data

        return CreateColumnParameterSet(
                ConcatenateValues(
                    ConcatenateIterables(
                        Select((data.GetPrimaryKeys(), data.GetColumns(), data.GetEntityColumns()), lambda columns: Select(columns, lambda column: column.GetColumnParameter()._AsColumn(self.GetDefaultTableName())))), # pyright: ignore[reportPrivateUsage]
                    ConcatenateIterables(
                        Select(data.GetForeignKeys(), lambda  column: column.GetColumnParameter()._AsColumns(self.GetDefaultTableName()).AsIterable())))) # pyright: ignore[reportPrivateUsage]

    def __CreateEntity(self, row: Iterator[object]) -> T:
        def __getEntity[_T: Entity](t: Type[_T], values: ITuple[object]) -> _T: return self.__context._GetMapper(t).GetOrCreateEntityFromKeys(values) # pyright: ignore[reportPrivateUsage]
        def _getEntity[_T: Entity](t: Type[_T], primaryKeys: Iterable[IDefaultColumn]) -> _T: return __getEntity(t, CreateTuple(Select(primaryKeys, lambda _: next(row))))
        def getEntity[_T: Entity](t: Type[_T]) -> _T: return _getEntity(t, _GetPrimaryKeys(t).AsIterable())

        data: _SelectionQueryData = self.__data
        obj: T = _getEntity(self.__type, data.GetPrimaryKeys())

        if obj.IsReady(): return obj
        
        _ProcessColumns(obj, row, data.GetColumns())
        _ProcessColumnsCore(obj, data.GetEntityColumns(), row, lambda args: __getEntity(args[0].GetColumnParameter().GetType(), MakeTuple(args[1])))

        for fk in data.GetForeignKeys(): _SetEntityValue(obj, fk, getEntity(fk.GetColumnParameter().GetType()))

        obj._Initialize() # pyright: ignore[reportPrivateUsage]

        return obj

    def Enumerate(self, results: Iterable[ISelectionQueryExecutionResult|None]) -> IEnumerable[T]:
        return CreateIteratorProvider(lambda: Select(ConcatenateItems(results), lambda row: self.__CreateEntity(iter(row))))
    def Iterate(self, *results: ISelectionQueryExecutionResult|None) -> IEnumerable[T]:
        return self.Enumerate(results)

def __InitializeStubs(items: Iterable[Entity], context: DataContextBase) -> Iterable[Entity]|None:
    def populate(stub: Entity) -> None:
        def getPKs() -> Iterable[IDefaultColumn]: return pks.AsIterable()
        
        t: IType[Entity] = TypeObject[Entity](type(stub))
        ks: IKeyedSet[IString, object]|None = keyedSetsByType.TryGetValue(t).TryGetValue()
        pks: ITuple[IDefaultColumn] = _GetPrimaryKeys(t.GetValue())

        if ks is None:
            ks = CreateKeyedSet(Select(getPKs(), lambda name: String(name.GetColumnParameter().GetColumnName())))

            keyedSetsByType.Add(t, ks)
        
        ks.TryAdd(CreateTuple(Select(getPKs(), lambda pk: _GetEntityValue(stub, pk))))

    keyedSetsByType: IDictionary[IType[Entity], IKeyedSet[IString, object]] = Dictionary[IType[Entity], IKeyedSet[IString, object]]()
    seen: ISet[IReference[Entity]] = Set[IReference[Entity]]()

    for parent in items:
        cols: _Columns = _GetColumns(parent)

        for col in ConcatenateEnumerables(cols.GetEntityColumns(), cols.GetForeignKeys()):
            stub: Entity|None = cast(Entity|None, _GetEntityValue(parent, col))

            if not (stub is None or stub.IsReady()) and seen.TryAdd(DefaultReference[Entity](stub)): populate(stub)
    
    if keyedSetsByType.GetCount() < 1: return None

    fresh: ICountableEnumerableList[Entity] = CountableEnumerableQueue[Entity]()

    for item in keyedSetsByType.AsIterable():
        hydrator: _Hydrator[Entity] = _Hydrator[Entity](item.GetKey().GetValue(), context)
        results: Generator[ISelectionQueryExecutionResult]|None = _GetTable(context, item.GetKey().GetValue()).SelectByKeys(hydrator.GetSelectionColumnSet(), item.GetValue())

        if results is not None: fresh.PushItems(hydrator.Enumerate(results).AsIterable())

    return None if fresh.GetCount() < 1 else fresh.AsIterable()

def TryInitializeStubs(items: Iterable[Entity]|None, context: DataContextBase, maxDepth: int = 1) -> bool:
    def validate(item: Entity) -> None:
        if not item.IsReady(): raise InvalidOperationError(f"{item} is not ready.")
    
    def check() -> bool:
        nonlocal maxDepth

        maxDepth -= 1

        return maxDepth > 0
    
    _EnsureNoUnresolvedRollbackError(context)
    
    if items is None or maxDepth < 1 or (items := __InitializeStubs(DoForEachItem(items, validate), context)) is None: return False
    
    while check() and (items := __InitializeStubs(items, context)) is not None: pass
    
    return True

class EntityCollection[T: Entity](Abstract):
    def __init__(self, context: DataContextBase) -> None:
        super().__init__()

        self.__context: DataContextBase = context
        self.__hydrator: _Hydrator[T] = _Hydrator[T](self._GetType(), context)
    
    @abstractmethod
    def _GetType(self) -> Type[T]:
        ...
    
    @final
    def __GetSelectionQuery(self) -> ISelectionQuery:
        return self.__context._GetConnection().GetFactoryProvider().GetQueryFactory().GetSelectionQuery( # pyright: ignore[reportPrivateUsage]
            TableParameterSet.CreateFromNames(String(self.__hydrator.GetDefaultTableName())),
            self.__hydrator.GetSelectionColumnSet())

    @final
    def __Run(self, query: ISelectionQuery) -> IEnumerable[T]:
        _EnsureNoUnresolvedRollbackError(self.__context)

        return self.__hydrator.Iterate(query.Execute())
    
    @final
    def Select(self) -> IEnumerable[T]:
        return self.__Run(self.__GetSelectionQuery())

    @final
    def Where(self, conditions: _IRoot) -> IEnumerable[T]:
        query: ISelectionQuery = self.__GetSelectionQuery()

        query.SetConditions(TryCreateConditionSetFromConditions(_Set(conditions, self.__hydrator.GetDefaultTableName())))

        return self.__Run(query)

class _RecordType(Enum):
    Null = 0
    Insert = 1
    Delete = 2

class _IReversibleRecord(IInterface):
    # Defining trait is Revert (not the insertion): both the INSERT record and the DELETE record
    # implement it, and the ledger sweeps them polymorphically to undo a rolled-back transaction.
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetRecordType(self) -> _RecordType:
        ...
    
    @abstractmethod
    def GetEntity(self) -> Entity:
        ...
    
    @abstractmethod
    def Revert(self) -> None:
        ...

class _ReversibleRecord[T: Entity](Abstract, _IReversibleRecord):
    def __init__(self, mapper: IEntityMapper[T], key: IEntityKey[IItem], entity: T) -> None:
        super().__init__()

        self.__mapper: IEntityMapper[T] = mapper
        self.__key: IEntityKey[IItem] = key
        self.__entity: T = entity
    
    @final
    def _GetMapper(self) -> IEntityMapper[T]:
        return self.__mapper
    
    @final
    def _GetKey(self) -> IEntityKey[IItem]:
        return self.__key

    @final
    def GetEntity(self) -> T: return self.__entity

class _InsertionRecord[TEntity: Entity, TValue](_ReversibleRecord[TEntity]):
    def __init__(self, mapper: IEntityMapper[TEntity], key: IEntityKey[IItem],
                 entity: TEntity, generatedColumn: _IAutoPrimaryKey[TEntity, TValue]|None = None,
                 oldValue: TValue|None = None) -> None:
        super().__init__(mapper, key, entity)

        self.__generatedColumn: _IAutoPrimaryKey[TEntity, TValue]|None = generatedColumn
        self.__oldValue = oldValue

    @final
    def GetRecordType(self) -> _RecordType: return _RecordType.Insert

    @final
    def Revert(self) -> None:
        self._GetMapper().Unregister(self._GetKey())

        generatedColumn: _IAutoPrimaryKey[TEntity, TValue]|None = self.__generatedColumn

        if generatedColumn is not None: generatedColumn._SetGeneratedValue(self.__entity, self.__oldValue) # pyright: ignore[reportPrivateUsage]

class _DeletionRecord[T: Entity](_ReversibleRecord[T]):
    # Strict mirror of _InsertionRecord: the revert-family record for a committed-deleted entity.
    def __init__(self, mapper: IEntityMapper[T], key: IEntityKey[IItem], entity: T, wasPersisted: bool, context: DataContextBase) -> None:
        super().__init__(mapper, key, entity)

        self.__wasPersisted: bool = wasPersisted
        self.__context: DataContextBase = context

    @final
    def GetRecordType(self) -> _RecordType: return _RecordType.Delete

    @final
    def Revert(self) -> None:
        # Capture-and-restore (not a blind re-apply): undo the framework mutation the DELETE emission
        # posted (identity-map removal + tombstone), so post-rollback memory is live again.
        self._GetMapper().Register(self._GetKey(), self.GetEntity())

        self.__entity._UnmarkDeleted() # pyright: ignore[reportPrivateUsage]

        # wasPersisted gates the persisted-set restoration: a DB-origin delete was never in
        # __persisted, so re-marking it unconditionally would be wrong.
        if self.__wasPersisted: self.__context._MarkPersisted(MakeSequence(self.__entity)) # pyright: ignore[reportPrivateUsage]

@final
class _Journal(Abstract):
    def __init__(self, context: DataContextBase) -> None:
        super().__init__()

        self.__context: DataContextBase = context
        self.__seen: ISet[IReference[Entity]] = Set[IReference[Entity]]()
        self.__ledger: IEnumerableList[_IReversibleRecord] = EnumerableQueue[_IReversibleRecord]() # Unified revert-family ledger: carries both inserts and deletes; Revert sweeps it to undo them.
        self.__updated: ISet[IReference[Entity]] = Set[IReference[Entity]]()
    
    def IsSeen(self, entity: Entity) -> bool:
        return self.__seen.Contains(DefaultReference[Entity](entity))
    def MarkSeen(self, entity: Entity) -> None:
        self.__seen.TryAdd(DefaultReference[Entity](entity))

    def RecordInserted[TEntity: Entity, TValue](self, mapper: IEntityMapper[TEntity], key: IEntityKey[IItem], entity: TEntity, generatedColumn: _IAutoPrimaryKey[TEntity, TValue]|None = None, oldValue: TValue|None = None) -> None:
        self.__ledger.Push(_InsertionRecord[TEntity, TValue](mapper, key, entity, generatedColumn, oldValue))
    def RecordUpdated(self, entity: Entity) -> None:
        self.__updated.TryAdd(DefaultReference[Entity](entity))
    def RecordDeleted[TEntity: Entity](self, mapper: IEntityMapper[TEntity], key: IEntityKey[IItem], entity: TEntity, wasPersisted: bool) -> None:
        self.__ledger.Push(_DeletionRecord[TEntity](mapper, key, entity, wasPersisted, self.__context))

    def Revert(self) -> None:
        for record in self.__ledger.AsGenerator(): record.Revert()

        # Update-records are leave-as-is: no in-memory revert. But an emitted-then-rolled-back
        # update leaves the entity diverging from the database, so the context is armed to force
        # an explicit resolution (Reverse/Retry) before any further database operation.
        if self.__updated.HasItems(): self.__context._ArmUnresolvedRollback(self.IterateUpdated()) # pyright: ignore[reportPrivateUsage]

    def IterateInserted(self) -> Iterable[Entity]:
        # The ledger now holds deletes too; the adder-promote consumer must see inserts only, else it
        # would pin a handle/baseline on a tombstoned entity. Filter to _InsertionRecord, widening to
        # the base record type (GetEntity is all the consumer needs) to keep the element type known.
        return WhereSelect(self.__ledger.AsIterable(), lambda record: record.GetRecordType() == _RecordType.Insert, lambda record: record.GetEntity())
    def IterateUpdated(self) -> Iterable[Entity]:
        return Select(self.__updated.AsIterable(), lambda reference: reference.GetValue())

@final
class _EntityEnumerationData(Abstract):
    def __init__(self, context: DataContextBase, journal: _Journal, onStack: ISet[IReference[Entity]]) -> None:
        super().__init__()

        self.__context: DataContextBase = context
        self.__journal: _Journal = journal
        self.__stack: ISet[IReference[Entity]] = onStack
    
    def GetContext(self) -> DataContextBase:
        return self.__context
    
    def GetJournal(self) -> _Journal:
        return self.__journal
    
    def GetStack(self) -> ISet[IReference[Entity]]:
        return self.__stack

def _TryAdd(entity: IReference[Entity], data: _EntityEnumerationData) -> bool:
    e: Entity = entity.GetValue()

    # Tombstone is terminal: any re-insertion (root or FK-target) raises. This guard MUST stay at the
    # head: a deleted DB-origin entity would otherwise be silently skipped by the DataBase-origin
    # branch below (return False) instead of raising. Placed here it covers both substrates and both
    # call-sites (root __Persist + _EntityEnumerable FK edge). This is the only line INSERT gains.
    if e._IsDeleted(): raise DeletedEntityError(e) # pyright: ignore[reportPrivateUsage]

    if _GetCookie(e).GetOrigin() == CookieOrigin.DataBase or data.GetContext()._IsInstancePersisted(e) or data.GetJournal().IsSeen(e): return False # pyright: ignore[reportPrivateUsage]
    
    if data.GetStack().TryAdd(entity): return True
    
    raise ForeignKeyCycleError(e)

@final
class _EntityEnumerable(RecursivelyEnumerable[IReference[Entity]]):
    def __init__(self, entity: Entity, data: _EntityEnumerationData) -> None:
        super().__init__()

        self.__entity: Entity = entity
        self.__data: _EntityEnumerationData = data
    
    def _AsRecursivelyEnumerable(self, container: IReference[Entity]) -> IEnumerable[IReference[Entity]]:
        return _EntityEnumerable(container.GetValue(), self.__data)
    
    def TryGetEnumerator(self) -> IEnumerator[IReference[Entity]]|None:
        e: Entity = self.__entity

        cols: _Columns = _GetColumns(e)

        return AsEnumerator(Include(Select(
            SelectWhereNotNone(
                ConcatenateEnumerables(
                    cols.GetEntityColumns(), cols.GetForeignKeys()),
                lambda edge: cast(Entity|None, _GetEntityValue(e, edge))),
            lambda e: DefaultReference[Entity](e)), GetTruthyPredicate(lambda entity: _TryAdd(entity, self.__data))))

def _Contains(items: IContainer[IString], column: IColumnAbstract) -> bool: return items.Contains(String(column.GetColumnParameter().GetColumnName()))

class _IColumnSelector(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def SelectColumns[T: IColumnAbstract](self, items: Iterable[T]) -> Iterable[T]:
        ...

@final
class _DefaultColumnSelector(Abstract, _IColumnSelector):
    def __init__(self) -> None: super().__init__()

    def SelectColumns[T: IColumnAbstract](self, items: Iterable[T]) -> Iterable[T]: return items
@final
class _UpdaterColumnSelector(Abstract, _IColumnSelector):
    def __init__(self, dirtyNonPrimaryKey: IContainer[IString]) -> None:
        super().__init__()

        self.__dirtyNonPrimaryKey: IContainer[IString] = dirtyNonPrimaryKey

    def SelectColumns[T: IColumnAbstract](self, items: Iterable[T]) -> Iterable[T]: return Include(items, lambda column: _Contains(self.__dirtyNonPrimaryKey, column))

_defaultColumnSelector: _IColumnSelector = _DefaultColumnSelector()

class _WriterBase(Abstract):
    def __init__(self, context: DataContextBase) -> None:
        super().__init__()

        self.__context: DataContextBase = context
    
    @final
    def _GetContext(self) -> DataContextBase:
        return self.__context

    @final
    def _AssembleRow(self, e: Entity, cols: _Columns, columnSelector: _IColumnSelector) -> IDictionary[IString, object]:
        def __add(columnParameter: IColumnParameterAbstract|ITableColumn, value: object) -> None:
            row.Add(String(columnParameter.GetColumnName()), value)

        def _add(column: IColumnAbstract, value: object) -> None: __add(column.GetColumnParameter(), value)

        def addColumns(columns: Iterable[IDefaultColumn]) -> None:
            for column in columnSelector.SelectColumns(columns): _add(column, _GetEntityValue(e, column))

        def addColumn(columns: ITuple[ITableColumn], index: int, value: object) -> None:
            __add(columns.GetAt(index), value)

        def getRange(columns: ICountable) -> range: return range(columns.GetCount())

        row: IDictionary[IString, object] = Dictionary[IString, object]()

        addColumns(WhereNotOfType(_IAutoPrimaryKey, cols.GetPrimaryKeys().AsIterable())) # type: ignore[type-abstract]
        addColumns(cols.GetColumns().AsIterable())

        target: Entity|None = None

        for entityColumn in columnSelector.SelectColumns(cols.GetEntityColumns().AsIterable()):
            target = cast(Entity|None, _GetEntityValue(e, entityColumn))

            _add(entityColumn, None if target is None else _GetEntityValue(target, _GetPrimaryKeys(target).GetAt(0)))

        for foreignKey in columnSelector.SelectColumns(cols.GetForeignKeys().AsIterable()):
            target = cast(Entity|None, _GetEntityValue(e, foreignKey))
            columns: ITuple[ITableColumn] = foreignKey.GetColumnParameter()._AsColumns(GetTypeName(e)) # pyright: ignore[reportPrivateUsage]

            if target is None:
                for i in getRange(columns): addColumn(columns, i, None)

            else:
                targetPrimaryKeys: ITuple[IDefaultColumn] = _GetPrimaryKeys(target)

                for i in getRange(columns): addColumn(columns, i, _GetEntityValue(target, targetPrimaryKeys.GetAt(i)))

        return row
    
    @final
    def _BuildKeyConditions(self, entity: Entity, primaryKeys: Iterable[IDefaultColumn]) -> IConditionParameterSet:
        # Shared by _Updater (WHERE of the UPDATE) and _Deleter (WHERE of the DELETE): a conjunction
        # of (pk = <current value>) equalities. The current PK value equals the baseline here (drift
        # is excluded upstream), so this WHERE targets exactly the persisted row.
        conditions: IConditionParameterSet|None = CreateConjunctionSet(Select(primaryKeys, lambda primaryKey: CreateDualResult(primaryKey.GetColumnParameter()._AsColumn(GetTypeName(entity)), CreateFieldParameterFromValue(Operator.Equals, _GetEntityValue(entity, primaryKey))))) # pyright: ignore[reportPrivateUsage]

        if conditions is None: raise InvalidOperationError("No primary key found.")

        return conditions
    
    @abstractmethod
    def Persist(self, entity: Entity, journal: _Journal) -> bool:
        ...
class _Writer(_WriterBase):
    def __init__(self, context: DataContextBase) -> None: super().__init__(context)
    
    @abstractmethod
    def Promote(self, journal: _Journal) -> None:
        ...

@final
class _Adder(_Writer):
    @final
    class _EnumerationHandler(RecursiveStackedEnumerationHandler[IReference[Entity]]):
        def __init__(self, onStack: ISet[IReference[Entity]]) -> None:
            super().__init__()

            self.__onStack: ISet[IReference[Entity]] = onStack

        def OnEnteringEnumerationLevel(self, item: IReference[Entity]) -> None:
            pass
        def OnExitingEnumerationLevel(self, cookie: IReference[Entity]) -> None:
            self.__onStack.Remove(cookie)
    
    def __init__(self, context: DataContextBase) -> None:
        super().__init__(context)

    def __GetAutoPrimaryKey(self, cols: _Columns) -> _IAutoPrimaryKey[Entity, object]|None:
        return cast(_IAutoPrimaryKey[Entity, object]|None, GetFirstOfType(_IAutoPrimaryKey, cols.GetPrimaryKeys().AsIterable()).TryGetValue()) # type: ignore[type-abstract]

    def __GetPrimaryKeyValues(self, e: Entity, cols: _Columns) -> ITuple[object]:
        return CreateTuple(Select(cols.GetPrimaryKeys().AsIterable(), lambda pk: _GetEntityValue(e, pk)))
    
    def __Persist(self, e: Entity, journal: _Journal, onStack: ISet[IReference[Entity]]) -> bool:
        def persist(ref: IReference[Entity]) -> bool:
            handler: _Adder._EnumerationHandler = _Adder._EnumerationHandler(onStack)
            entity: Entity = ref.GetValue()

            for e in AppendItem(Select(_EntityEnumerable(entity, data).GetRecursiveStackedEnumerator(EnumerationOrder.LIFO, handler).AsIterator(), lambda e: e.GetValue()), entity):
                cols: _Columns = _GetColumns(e)
                autoPrimaryKey: _IAutoPrimaryKey[Entity, object]|None = self.__GetAutoPrimaryKey(cols)

                # Capture the placeholder BEFORE write-back.
                oldValue: object|None = None if autoPrimaryKey is None else _GetEntityValue(e, autoPrimaryKey)

                row: IDictionary[IString, object] = self._AssembleRow(e, cols, _defaultColumnSelector)

                mapper: IEntityMapper[Entity] = context._GetMapper(type(e)) # pyright: ignore[reportPrivateUsage]
                key: IEntityKey[IItem]|None = None

                if autoPrimaryKey is None:
                    key = mapper.GetKey(self.__GetPrimaryKeyValues(e, cols))

                    if mapper.TryGetEntity(key) is not None: raise DuplicateIdentityError(e)

                result: IInsertionQueryExecutionResult = _GetTable(context, e).Insert(row)

                try:
                    if autoPrimaryKey is not None: autoPrimaryKey._SetGeneratedValue(e, result.GetLastRowId()) # pyright: ignore[reportPrivateUsage]
                
                finally: result.Dispose()

                if key is None: key = mapper.GetKey(self.__GetPrimaryKeyValues(e, cols))

                mapper.Register(key, e)

                journal.MarkSeen(e)
                journal.RecordInserted(mapper, key, e, autoPrimaryKey, oldValue)

            return True
        
        context: DataContextBase = self._GetContext()
        data: _EntityEnumerationData = _EntityEnumerationData(context, journal, onStack)
        ref: IReference[Entity] = DefaultReference[Entity](e)
        
        return persist(ref) if _TryAdd(ref, data) else False
    
    def Persist(self, entity: Entity, journal: _Journal) -> bool:
        return self.__Persist(entity, journal, Set[IReference[Entity]]())
    def PersistRange(self, items: Iterable[Entity], journal: _Journal) -> bool|None:
        return Scan(items, lambda item: self.__Persist(item, journal, Set[IReference[Entity]]()))

    def Promote(self, journal: _Journal) -> None:
        context: DataContextBase = self._GetContext()

        # Promote pins the context handle on each freshly inserted entity (so it becomes a valid
        # UPDATE target) and re-baselines its cookie, since the committed state is now the baseline.
        for entity in journal.IterateInserted(): _SetEntityContext(entity, context)._CommitChanges() # pyright: ignore[reportPrivateUsage]
        
        context._MarkPersisted(journal.IterateInserted()) # pyright: ignore[reportPrivateUsage]

@final
class _Updater(_Writer):
    def __init__(self, context: DataContextBase) -> None:
        super().__init__(context)

    def Persist(self, entity: Entity, journal: _Journal) -> bool:
        cols: _Columns = _GetColumns(entity)
        dirty: Iterable[IString] = _GetCookie(entity).GetDirtyColumns().AsIterable()

        primaryKeys: Iterable[IDefaultColumn] = cols.GetPrimaryKeys().AsIterable()
        primaryKeyNames: ISet[IString] = CreateSet(Select(primaryKeys, lambda primaryKey: String(primaryKey.GetColumnParameter().GetColumnName())))

        if HasAny(dirty, primaryKeyNames.Contains): raise PrimaryKeyMutationError(entity)

        dirtyNonPrimaryKey: ISet[IString] = CreateSet(Exclude(dirty, lambda name: primaryKeyNames.Contains(name)))

        if dirtyNonPrimaryKey.IsEmpty(): return False

        for target in WhereSelect(ConcatenateEnumerables(cols.GetEntityColumns(), cols.GetForeignKeys()), lambda column: _Contains(dirtyNonPrimaryKey, column), lambda column: cast(Entity|None, _GetEntityValue(entity, column))):
            if target is not None and _TryGetEntityContext(target) is None: raise UnpersistedReferenceError(target)

        values: IDictionary[IString, object] = self._AssembleRow(entity, cols, _UpdaterColumnSelector(dirtyNonPrimaryKey))
        result: IInsertionQueryExecutionResult = _GetTable(self._GetContext(), entity).Update(values, self._BuildKeyConditions(entity, primaryKeys))

        try:
            if result.GetRowCount() == 0: raise RowVanishedError(entity)

        finally: result.Dispose()

        journal.RecordUpdated(entity)

        return True

    def Promote(self, journal: _Journal) -> None:
        for entity in journal.IterateUpdated(): _GetCookie(entity)._CommitChanges() # pyright: ignore[reportPrivateUsage]

@final
class _Deleter(_WriterBase):
    # Much simpler than _Updater: no SET dirty-tracking, no row assembly, no FK-target check. The
    # cookie substrate (App/DB) is out of play; the only new state is the cookie tombstone.
    def __init__(self, context: DataContextBase) -> None: super().__init__(context)

    def Persist(self, entity: Entity, journal: _Journal) -> bool:
        primaryKeys: Iterable[IDefaultColumn] = _GetColumns(entity).GetPrimaryKeys().AsIterable()

        # PK-drift guard (D1): the sole use of dirty-tracking in DELETE. A drifted PK (App-origin
        # struct bypass) would aim the WHERE at the wrong row; refuse it. DB-origin PKs are not
        # driftable. The WHERE is then built from the current PK, which here equals the baseline.
        primaryKeyNames: ISet[IString] = CreateSet(Select(primaryKeys, lambda primaryKey: String(primaryKey.GetColumnParameter().GetColumnName())))

        if HasAny(_GetCookie(entity).GetDirtyColumns().AsIterable(), primaryKeyNames.Contains): raise PrimaryKeyMutationError(entity)

        context: DataContextBase = self._GetContext()
        result: IQueryExecutionResult = _GetTable(context, entity).Delete(self._BuildKeyConditions(entity, primaryKeys))

        try:
            # DB<->memory invariant (C5), identical to UPDATE: 0 rows means the row vanished
            # out-of-band. Raise BEFORE any memory marking, so a DELETE that removed nothing never
            # tombstones; the exception dooms the tx and the entity stays intact.
            if result.GetRowCount() == 0: raise RowVanishedError(entity)

        finally: result.Dispose()

        # Mark at emission: the entity still functions (= would lie); act immediately.
        mapper: IEntityMapper[Entity] = context._GetMapper(type(entity)) # pyright: ignore[reportPrivateUsage]
        key: IEntityKey[IItem] = mapper.GetKey(CreateTuple(Select(primaryKeys, lambda primaryKey: _GetEntityValue(entity, primaryKey))))

        # Captured before unmarking: True for App-origin-promoted, False for DB-origin (never in __persisted).
        wasPersisted: bool = context._IsInstancePersisted(entity) # pyright: ignore[reportPrivateUsage]

        mapper.Unregister(key)
        entity._MarkDeleted() # pyright: ignore[reportPrivateUsage]

        if wasPersisted: context._UnmarkPersisted(entity) # pyright: ignore[reportPrivateUsage]

        journal.RecordDeleted(mapper, key, entity, wasPersisted)

        return True

class ITransaction(ITransactionControl, IDisposable):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryAdd(self, item: Entity) -> bool:
        ...
    @abstractmethod
    def TryAddRange(self, items: Iterable[Entity]) -> bool|None:
        ...

    @abstractmethod
    def TryUpdate(self, item: Entity) -> bool:
        ...

    @abstractmethod
    def Delete(self, item: Entity) -> None:
        ...

class _ITransaction(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsActive(self) -> bool:
        ...

    @abstractmethod
    def Begin(self) -> bool:
        ...

    @abstractmethod
    def TryAdd(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
        ...
    @abstractmethod
    def TryAddRange(self, items: Iterable[Entity]) -> bool|tuple[BaseException, _ITransaction]|None:
        ...
    
    @abstractmethod
    def TryUpdate(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
        ...

    @abstractmethod
    def Delete(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
        ...

    @abstractmethod
    def Commit(self) -> bool|tuple[BaseException, _ITransaction]:
        ...
    @abstractmethod
    def Rollback(self) -> bool:
        ...
    
    @abstractmethod
    def OnExiting(self, exc: BaseException|None) -> bool:
        ...
    @abstractmethod
    def Dispose(self) -> tuple[_ITransaction, BaseException|None]:
        ...

class _TransactionAbstract(Abstract, _ITransaction):
    def __init__(self) -> None:
        super().__init__()
    
    def _OnExiting(self) -> None:
        pass
    
    @final
    def OnExiting(self, exc: BaseException|None) -> bool:
        if exc is None: return False
        
        self._OnExiting()
        
        return True
class _TransactionBase(_TransactionAbstract):
    def __init__(self, control: ITransactionControl, journal: _Journal) -> None:
        super().__init__()

        self.__control: ITransactionControl = control
        self.__journal: _Journal = journal
    
    @final
    def _GetTransactionControl(self) -> ITransactionControl:
        return self.__control
    @final
    def _GetJournal(self) -> _Journal:
        return self.__journal
    
    @final
    def _Commit(self) -> bool:
        return self._GetTransactionControl().Commit()
    @final
    def _Rollback(self) -> bool:
        try: return self._GetTransactionControl().Rollback()
        finally: self._GetJournal().Revert()

    @final
    def IsActive(self) -> bool:
        return self._GetTransactionControl().IsActive()

    @final
    def Begin(self) -> bool: return self._GetTransactionControl().Begin()

    @final
    def Rollback(self) -> bool: return self._Rollback() if self.IsActive() else False

    @final
    def _OnExiting(self) -> None:
        try:
            if self.IsActive(): self._Rollback()
        
        except: pass

@final
class _Transaction(Abstract, ITransaction):
    @final
    class _Active(_TransactionBase):
        def __init__(self, context: DataContextBase, control: ITransactionControl, adder: _Adder, updater: _Updater, deleter: _Deleter) -> None:
            super().__init__(control, _Journal(context))
            
            self.__adder: _Adder = adder
            self.__updater: _Updater = updater
            self.__deleter: _Deleter = deleter
        
        def __GetTransaction(self, e: BaseException) -> tuple[BaseException, _ITransaction]:
            return (e, _Transaction._Doomed(self._GetTransactionControl(), self._GetJournal()))
        
        def __Promote(self) -> None:
            def promote(writer: _Writer) -> None: writer.Promote(self._GetJournal())

            promote(self.__adder)
            promote(self.__updater)
        
        def __TryAdd[T](self, item: T, action: Callable[[T, _Journal], bool|None]) -> bool|tuple[BaseException, _ITransaction]|None:
            if self.IsActive():
                try: return action(item, self._GetJournal())
                except BaseException as e: return self.__GetTransaction(e)
            
            return None
        def __TryPersist(self, item: Entity, writer: _WriterBase) -> bool|tuple[BaseException, _ITransaction]:
            result: bool|tuple[BaseException, _ITransaction]|None = self.__TryAdd(item, writer.Persist)
            
            return result if isinstance(result, tuple) else result is True
        
        def TryAdd(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
            return self.__TryPersist(item, self.__adder)
        def TryAddRange(self, items: Iterable[Entity]) -> bool|tuple[BaseException, _ITransaction]|None: return self.__TryAdd(items, self.__adder.PersistRange)

        def TryUpdate(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
            return self.__TryPersist(item, self.__updater)

        def Delete(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]:
            return self.__TryPersist(item, self.__deleter)

        def Commit(self) -> bool|tuple[BaseException, _ITransaction]:
            try:
                if self._Commit():
                    self.__Promote()
                    
                    return True
                
                return False
            
            except BaseException as e:
                return self.__GetTransaction(e)
        
        def Dispose(self) -> tuple[_ITransaction, BaseException|None]:
            def getResult(e: BaseException|None) -> tuple[_ITransaction, BaseException|None]: return (_Transaction._Disposed(), e)
            
            def commit() -> bool|BaseException:
                try: return self._Commit()
                
                except BaseException as e:
                    try: self._Rollback()
                    except: pass
                    
                    return e
            
            if self.IsActive():
                result: bool|BaseException = commit()
                
                if isinstance(result, BaseException): return getResult(result)

                if result: self.__Promote()
            
            return getResult(None)
    @final
    class _Doomed(_TransactionBase):
        def __init__(self, control: ITransactionControl, journal: _Journal) -> None: super().__init__(control, journal)

        def __EnsureInactive(self) -> None:
            if self.IsActive(): raise InvalidOperationError("Transaction is doomed.")
        def __CheckIsActive(self) -> bool:
            self.__EnsureInactive()

            return False

        def TryAdd(self, item: Entity) -> bool: return self.__CheckIsActive()
        def TryAddRange(self, items: Iterable[Entity]) -> bool|None:
            self.__EnsureInactive()

            return None
        
        def TryUpdate(self, item: Entity) -> bool: return self.__CheckIsActive()
        
        def Delete(self, item: Entity) -> bool: return self.__CheckIsActive()
        
        def Commit(self) -> bool: return self.__CheckIsActive()
        
        def Dispose(self) -> tuple[_ITransaction, BaseException|None]:
            def getResult(e: BaseException|None) -> tuple[_ITransaction, BaseException|None]: return (_Transaction._Disposed(), e)
            
            if self.IsActive():
                try: self._Rollback()
                except BaseException as e: return getResult(e)
            
            return getResult(None)
    @final
    class _Disposed(_TransactionAbstract):
        def __init__(self) -> None: super().__init__()

        def IsActive(self) -> bool: return False
        
        def Begin(self) -> bool: return False
        
        def TryAdd(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]: return False
        def TryAddRange(self, items: Iterable[Entity]) -> bool|tuple[BaseException, _ITransaction]|None: return None

        def TryUpdate(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]: return False
        
        def Delete(self, item: Entity) -> bool|tuple[BaseException, _ITransaction]: return False
        
        def Commit(self) -> bool|tuple[BaseException, _ITransaction]: return False
        def Rollback(self) -> bool: return False
        
        def Dispose(self) -> tuple[_ITransaction, BaseException|None]: return (self, None)
    
    def __init__(self, cookie: _ITransactionCookie, control: ITransactionControl, adder: _Adder, updater: _Updater, deleter: _Deleter) -> None:
        def tryInitialize() -> bool:
            def dispose() -> None:
                self.__dispose = NoAction
                
                cookie.Unregister()
            
            self.__tryInitialize = BoolTrue
            self.__dispose = dispose
            
            return cookie.TryRegister(self)
        
        super().__init__()
        
        context: DataContextBase = cookie.GetContext()
        
        self.__context: DataContextBase = context
        self.__transaction: _ITransaction = _Transaction._Active(context, control, adder, updater, deleter)
        
        self.__tryInitialize: Function[bool] = tryInitialize # type: ignore[no-redef]
        self.__dispose: Action = NoAction # type: ignore[no-redef]
    
    def __Process[T: bool|None](self, func: Converter[_ITransaction, T|tuple[BaseException, _ITransaction]]) -> T:
        result: T|tuple[BaseException, _ITransaction] = func(self.__transaction)
        
        if isinstance(result, tuple):
            self.__transaction = result[1]
            
            raise result[0]
        
        return result
    def __Write[T: bool|None](self, func: Converter[_ITransaction, T|tuple[BaseException, _ITransaction]]) -> T:
        _EnsureNoUnresolvedRollbackError(self.__context)
        
        return self.__Process(func)
    
    def Initialize(self) -> None:
        if not self.__tryInitialize(): raise GetActiveTransactionError()
    def Dispose(self) -> None:
        result: tuple[_ITransaction, BaseException|None] = self.__transaction.Dispose()
        
        self.__dispose()

        self.__transaction = result[0]

        e: BaseException|None = result[1]

        if e is not None: raise e

    def _OnExiting(self, excType: type[BaseException]|None, exc: BaseException|None, traceback: TracebackType|None) -> bool|None: return None if self.__transaction.OnExiting(exc) else False
    
    def IsActive(self) -> bool: return self.__transaction.IsActive()
    
    def Begin(self) -> bool:
        return self.__tryInitialize() and self.__transaction.Begin()

    def TryAdd(self, item: Entity) -> bool: return self.__Write(lambda transaction: transaction.TryAdd(item))
    def TryAddRange(self, items: Iterable[Entity]) -> bool|None: return self.__Write(lambda transaction: transaction.TryAddRange(items))
    def TryUpdate(self, item: Entity) -> bool: return self.__Write(lambda transaction: transaction.TryUpdate(item))
    def Delete(self, item: Entity) -> None: self.__Write(lambda transaction: transaction.Delete(item)) # the bool from __Write (T = bool) is discarded -> None

    def Commit(self) -> bool: return self.__Process(lambda transaction: transaction.Commit())
    def Rollback(self) -> bool: return self.__transaction.Rollback()

class _ITransactionCookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetContext(self) -> DataContextBase:
        ...
    
    @abstractmethod
    def TryRegister(self, transaction: ITransaction) -> bool:
        ...
    @abstractmethod
    def Unregister(self) -> None:
        ...

def SelectEntities(entities: Iterable[Entity]) -> Iterable[IReference[Entity]]:
    return Select(entities, lambda entity: DefaultReference[Entity](entity))

class DataContextBase(Abstract):
    @final
    class __Cookie(Abstract, _ITransactionCookie):
        def __init__(self, context: DataContextBase) -> None:
            super().__init__()

            self.__context: DataContextBase = context
        
        def GetContext(self) -> DataContextBase: return self.__context
        
        def TryRegister(self, transaction: ITransaction) -> bool: return self.GetContext()._TryRegisterTransaction(transaction)
        def Unregister(self) -> None: self.GetContext()._UnregisterTransaction()
    
    def __init__(self) -> None:
        super().__init__()

        self.__items: IDictionary[IType[Entity], IEntityMapperBase[Entity]] = Dictionary[IType[Entity], IEntityMapperBase[Entity]]()

        self.__persisted: ISet[IReference[Entity]] = Set[IReference[Entity]]()
        self.__unresolved: ISet[IReference[Entity]]|None = None

        self.__transaction: ITransaction|None = None

    @abstractmethod
    def _GetConnection(self) -> IConnection:
        ...
    
    @final
    def _TryRegisterTransaction(self, transaction: ITransaction|None) -> bool:
        if self.__transaction is None:
            self.__transaction = transaction

            return True
        
        return False
    @final
    def _UnregisterTransaction(self) -> None:
        self.__transaction = None

    @final
    def _IsInstancePersisted(self, entity: Entity) -> bool:
        return self.__persisted.Contains(DefaultReference[Entity](entity))
    @final
    def _MarkPersisted(self, entities: Iterable[Entity]) -> None:
        self.__persisted.TryAddRange(SelectEntities(entities))
    @final
    def _UnmarkPersisted(self, entity: Entity) -> None:
        # Called only when wasPersisted is True (the element is present, so Remove is safe).
        self.__persisted.Remove(DefaultReference[Entity](entity))

    @final
    def _ArmUnresolvedRollback(self, entities: Iterable[Entity]) -> None:
        self.__unresolved = CreateSet(SelectEntities(entities))
    @final
    def IsBlocked(self) -> bool:
        return self.__unresolved is not None

    @final
    def Reverse(self) -> None:
        unresolved: ISet[IReference[Entity]]|None = self.__unresolved

        if unresolved is None: return

        # Resolution exit: abandon the pending in-memory mutations of every diverging entity by
        # restoring its baseline, then clear the block.
        for reference in unresolved.AsIterable(): _GetCookie(reference.GetValue())._RevertChanges() # pyright: ignore[reportPrivateUsage]

        self.__unresolved = None
    @final
    def Retry(self) -> bool:
        unresolved: ISet[IReference[Entity]]|None = self.__unresolved

        if unresolved is None: return True

        self.__unresolved = None

        # Resolution exit: re-emit the diverging updates in a fresh transaction. The block is
        # cleared up front so the re-emission is not itself gated; on any failure the rolled-back
        # transaction is re-armed with the full set (its own journal would only re-arm the subset
        # it managed to record before failing).
        entities: Iterable[Entity] = CreateTuple(Select(unresolved.AsIterable(), lambda reference: reference.GetValue())).AsIterable()

        transaction: ITransaction = self.BeginTransaction()

        try:
            for entity in entities: transaction.TryUpdate(entity)

            transaction.Dispose()

        except BaseException:
            try: transaction.Dispose()
            except BaseException: pass

            self._ArmUnresolvedRollback(entities)

            return False

        return True

    @final
    def _GetMapper[T: Entity](self, t: Type[T]) -> IEntityMapper[T]:
        _t: IType[T] = TypeObject[T](t)
        mapper: IEntityMapper[T]|None = cast(IEntityMapper[T]|None, self.__items.TryGetValue(_t).TryGetValue())

        if mapper is None: self.__items.Add(_t, mapper := EntityMapper[T](t, self))
        
        return mapper
    
    @final
    def CreateTransaction(self) -> ITransaction: return _Transaction(DataContextBase.__Cookie(self), self._GetConnection().CreateTransactionControl(), _Adder(self), _Updater(self), _Deleter(self))
    @final
    def BeginTransaction(self) -> ITransaction:
        transaction: ITransaction = self.CreateTransaction()

        transaction.Begin()
        
        return transaction
    
    @final
    def TryGetActiveTransaction(self) -> ITransaction|None:
        return self.__transaction
class DataContext(DataContextBase):
    def __init__(self, connection: IConnection) -> None:
        super().__init__()

        self.__connection: IConnection = connection

    @final
    def _GetConnection(self) -> IConnection: return self.__connection