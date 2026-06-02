from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Iterator
from enum import Enum
from typing import overload, final, Callable, Any, Type, cast



from WinCopies import IInterface, Abstract

from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Abstraction.Collection import CreateTuple, MakeTuple, CreateHashableTuple
from WinCopies.Collections.Abstraction.Collection.Mapping import Dictionary, CreateDictionary
from WinCopies.Collections.Core import IReadOnlyIndexable
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, EnumeratorBase, Enumerable, IteratorProvider, GetEmptyEnumerable, AsEnumerator, GetEnumeratorInactiveError
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursivelyIterableProvider, CreateRecursivelyIterableProvider
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursiveEnumerator, StackedRecursiveEnumerator
from WinCopies.Collections.Expression import IConnector, ICompositeExpression, ICompositeExpressionNodeBase, ICompositeExpressionNode, ICompositeExpressionRoot, CompositeExpressionValueNode, CompositeExpressionNode, CompositeExpressionValueRoot, CompositeExpressionRoot
from WinCopies.Collections.Extensions import ITuple, IHashableTuple, IReadOnlySet, IReadOnlyDictionary, IDictionary
from WinCopies.Collections.Generation import IIterator
from WinCopies.Collections.Iteration import Concatenate as ConcatenateIterables, ConcatenateValues, Select, WhereOfType
from WinCopies.Collections.Linked.Doubly import IList, CreateList
from WinCopies.Collections.Loop import DoForEachItem

from WinCopies.Typing import IDisposable, InvalidOperationError
from WinCopies.Typing.Delegate import IFunction, IMethodBase, Method, Predicate, Converter, Selector, IInitializableConverter, ValueFunction, ValueFunctionUpdater, ValueConverterUpdater
from WinCopies.Typing.Object import IItem, IValueItem, IValueObject, IItemObject, IReference, Reference, IString, String, IType, Type as TypeObject, Map
from WinCopies.Typing.Pairing import IKeyValuePair, CreateKeyValuePair
from WinCopies.Typing.Reflection import GetterBase, SetterBase, Property, IFunctionProvider, IGetterProvider, IPropertyProvider, IReadOnlyProperty, IProperty, ReadOnlyPropertyDecorator, PropertyDecorator



from WinCopies.Data import Operator, ConditionalOperator, IOperandValue, IOperand, ITableColumn, Operand, SetOperand
from WinCopies.Data.Abstract import IConnection
from WinCopies.Data.Parameter import IParameter, FieldParameter
from WinCopies.Data.Query import ISelectionQuery, ISelectionQueryExecutionResult
from WinCopies.Data.Set import IFieldConditionRecursivelyEnumerable, IFieldParameterSetItem
from WinCopies.Data.Set.Extensions import TableParameterSet, CreateColumnParameterSet, TryCreateConditionSetFromConditions

@final
class _TableColumn(Abstract, ITableColumn):
    def __init__(self, columnName: str, tableName: str) -> None:
        super().__init__()

        self.__columnName: str = columnName
        self.__tableName: str = tableName
    
    def GetColumnName(self) -> str:
        return self.__columnName
    
    def GetTableName(self) -> str:
        return self.__tableName

@final
class _ColumnParameterUpdater(ValueConverterUpdater[str, ITableColumn]):
    def __init__(self, parameter: IColumnParameterAbstract, updater: Method[IInitializableConverter[str, ITableColumn]]) -> None:
        super().__init__(updater)

        self.__parameter: IColumnParameterAbstract = parameter
    
    def ConvertValue(self, value: str) -> ITableColumn:
        return _TableColumn(self.__parameter.GetColumnName(), value)
@final
class _ForeignKeyParameterUpdater(ValueConverterUpdater[str, ITuple[ITableColumn]]):
    def __init__(self, columnNames: Iterable[str], updater: Method[IInitializableConverter[str, ITuple[ITableColumn]]]) -> None:
        super().__init__(updater)

        self.__columnNames: Iterable[str] = columnNames
    
    def ConvertValue(self, value: str) -> ITuple[ITableColumn]:
        return CreateTuple(Select(self.__columnNames, lambda columnName: _TableColumn(columnName, value)))

class IColumnParameterCookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsColumn(self, tableName: str) -> ITableColumn:
        pass

class _IDataParameter(IKeyValuePair[IColumnParameterCookie, IParameter[IOperandValue]|None]):
    def __init__(self) -> None:
        super().__init__()

class _ParameterBase[T](Abstract, _IDataParameter):
    def __init__(self, cookie: IColumnParameterCookie, operand: IOperand[T]) -> None:
        super().__init__()

        self.__columnParameter: IColumnParameterCookie = cookie
        self.__parameter: IParameter[IOperandValue] = FieldParameter[T](operand)
    
    def IsKeyValuePair(self) -> bool:
        return False
    
    def GetKey(self) -> IColumnParameterCookie:
        return self.__columnParameter
    def GetValue(self) -> IParameter[IOperandValue]|None:
        return self.__parameter

@final
class _Parameter[T](_ParameterBase[T]):
    def __init__(self, cookie: IColumnParameterCookie, operator: Operator, value: T) -> None:
        super().__init__(cookie, Operand[T](operator, value))
@final
class _SetParameter[T: IValueItem](_ParameterBase[IReadOnlySet[T]]):
    def __init__(self, cookie: IColumnParameterCookie, values: IReadOnlySet[T]) -> None:
        super().__init__(cookie, SetOperand[T](values))

class _INode(ICompositeExpressionNode[_IDataParameter, ConditionalOperator]):
    def __init__(self) -> None:
        super().__init__()
class _IRoot(ICompositeExpressionRoot[_IDataParameter, ConditionalOperator]):
    def __init__(self) -> None:
        super().__init__()

@final
class _ValueNode(CompositeExpressionValueNode[_IDataParameter, ConditionalOperator], _INode):
    def __init__(self, parameter: _IDataParameter) -> None:
        super().__init__(parameter)
@final
class _Node(CompositeExpressionNode[_IDataParameter, ConditionalOperator], _INode):
    def __init__(self, node: _INode) -> None:
        super().__init__(node)

@final
class _ValueRoot(CompositeExpressionValueRoot[_IDataParameter, ConditionalOperator], _IRoot):
    def __init__(self, parameter: _IDataParameter) -> None:
        super().__init__(parameter)
@final
class _Root(CompositeExpressionRoot[_IDataParameter, ConditionalOperator], _IRoot):
    def __init__(self, x: _INode) -> None:
        super().__init__(x)

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

def _TryGetConnector(connector: IConnector[_IDataParameter, ConditionalOperator]|None) -> ConditionalOperator|None:
    return None if connector is None else connector.GetConnector()

@final
class _Expression(Abstract, IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]):
    def __init__(self, expression: ICompositeExpression[_IDataParameter, ConditionalOperator], tableName: str) -> None:
        super().__init__()

        self.__expression: ICompositeExpression[_IDataParameter, ConditionalOperator] = expression
        self.__tableName: str = tableName
    
    def TryGetFieldParameter(self) -> IKeyValuePair[ITableColumn, IParameter[IOperandValue]|None]|None:
        parameter: _IDataParameter|None = self.__expression.TryGetValue().TryGetValue()

        return None if parameter is None else CreateKeyValuePair(parameter.GetKey()._AsColumn(self.__tableName), parameter.GetValue()) # pyright: ignore[reportPrivateUsage]
    
    def TryGetPreviousOperator(self) -> ConditionalOperator|None:
        return _TryGetConnector(self.__expression.GetPrevious())
    def TryGetNextOperator(self) -> ConditionalOperator|None:
        return _TryGetConnector(self.__expression.GetNext())
    
    def TryGetItems(self) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        expression: ICompositeExpressionNode[_IDataParameter, ConditionalOperator]|None = self.__expression.TryGetItems()

        return None if expression is None else IteratorProvider[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]](lambda: Select(expression.AsIterable(), lambda expression: _Expression(expression, self.__tableName)))

def _GetEnumerable(enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
    items: IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = enumerationItems.TryGetItems()

    return GetEmptyEnumerable() if items is None else items

@final
class _RecursiveEnumerator(RecursiveEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]], handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> None:
        super().__init__(enumerator, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
        return _GetEnumerable(enumerationItems)
@final
class _StackedRecursiveEnumerator(StackedRecursiveEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]], enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> None:
        super().__init__(enumerator, enumerationOrder, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
        return _GetEnumerable(enumerationItems)

def _TryGetRecursiveEnumerator(enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
    return None if enumerator is None else _RecursiveEnumerator(enumerator, handler)
def _TryGetRecursiveStackedEnumerator(enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None, enumerationOrder: EnumerationOrder, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
    return None if enumerator is None or enumerationOrder == EnumerationOrder.Null else _StackedRecursiveEnumerator(enumerator, enumerationOrder, handler)

def _TryGetEnumerator(expressionRoot: IFieldConditionRecursivelyEnumerable[ITableColumn], enumerationOrder: EnumerationOrder, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
    if enumerationOrder == EnumerationOrder.Null:
        return None
    
    match enumerationOrder:
        case EnumerationOrder.FIFO:
            return _TryGetRecursiveEnumerator(expressionRoot.TryGetEnumerator(), handler)
        case EnumerationOrder.LIFO:
            return expressionRoot.TryGetRecursiveStackedEnumerator(EnumerationOrder.LIFO, None if handler is None else handler.AsStackHandler())
        case _:
            raise ValueError(enumerationOrder)

@final
class _Set(Abstract, IFieldConditionRecursivelyEnumerable[ITableColumn]):
    def __init__(self, conditions: _IRoot, tableName: str) -> None:
        super().__init__()

        self.__conditions: _IRoot = conditions
        self.__tableName: str = tableName
        self.__iterable: RecursivelyIterableProvider[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]] = CreateRecursivelyIterableProvider(self)
    
    @final
    def AsRecursivelyEnumerable(self) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
        return self.__iterable.AsRecursivelyEnumerable()
    
    @final
    def AsIterable(self) -> Iterable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
        return self.__iterable.AsIterable()
    
    def TryGetEnumerator(self) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        return AsEnumerator(Select(self.__conditions.AsIterable(), lambda expression: _Expression(expression, self.__tableName)))
    
    @final
    def TryGetRecursiveEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        return _TryGetEnumerator(self, enumerationOrder, handler)
    @final
    def TryGetRecursiveStackedEnumerator(self, enumerationOrder: EnumerationOrder = EnumerationOrder.FIFO, handler: IRecursiveStackedEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        return _TryGetRecursiveStackedEnumerator(self.TryGetEnumerator(), enumerationOrder, handler)

class Role(Enum):
    Null = 0
    PrimaryKey = 1
    ForeignKey = 2

class IColumnCondition[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def ToConditionParameter(self, operator: Operator, value: T) -> _IDataParameter|_ValueNode:
        pass
    @abstractmethod
    def ToConditionNode(self, operator: Operator, value: T) -> _ValueNode:
        pass
    @abstractmethod
    def ToConditionRoot(self, operator: Operator, value: T) -> _ValueRoot:
        pass
class IColumnSetCondition[T](IColumnCondition[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[T]]) -> _IDataParameter|_ValueNode:
        pass
    @abstractmethod
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[T]]) -> _ValueNode:
        pass
    @abstractmethod
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[T]]) -> _ValueRoot:
        pass

class IColumnParameterAbstract(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetColumnRole(self) -> Role:
        pass
    
    @abstractmethod
    def GetColumnName(self) -> str:
        pass
    
    @abstractmethod
    def _SetTableName(self, tableName: str) -> None:
        pass
class IEntityColumnParameterAbstract(IColumnParameterAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[Entity]:
        pass

class IColumnParameterBase(IColumnParameterAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsColumn(self, tableName: str) -> ITableColumn:
        pass
class IEntityColumnParameterBase(IColumnParameterBase, IEntityColumnParameterAbstract):
    def __init__(self) -> None:
        super().__init__()

class IColumnParameter[T](IColumnSetCondition[T], IColumnParameterBase):
    def __init__(self) -> None:
        super().__init__()
class IEntityColumnParameter[T: Entity](IColumnCondition[T], IEntityColumnParameterBase):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        pass

class IForeignKeyParameterAbstract(IEntityColumnParameterAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetColumnRole(self) -> Role:
        return Role.ForeignKey
class IForeignKeyParameterBase(IForeignKeyParameterAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsColumns(self, tableName: str) -> ITuple[ITableColumn]:
        pass
class IForeignKeyParameter[T: Entity](IForeignKeyParameterBase, IColumnCondition[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        pass

class IParameterKey(IReference[IColumnParameterAbstract]):
    def __init__(self) -> None:
        super().__init__()
class ParameterKey(Reference[IColumnParameterAbstract], IParameterKey):
    def __init__(self, parameter: IColumnParameterAbstract) -> None:
        super().__init__(parameter)
    
    def ToString(self) -> str:
        return self.GetValue().GetColumnName()

def _GetColumns(t: Type[Entity]) -> _Columns:
    return t._GetColumns() # pyright: ignore[reportPrivateUsage]

def _GetPrimaryKeys(t: Type[Entity]) -> ITuple[IDefaultColumn]:
    return _GetColumns(t).GetPrimaryKeys()

class IColumnParameterDelegate[TValue](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode:
        pass
    @abstractmethod
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        pass
    @abstractmethod
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot:
        pass
    
    @abstractmethod
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter|_ValueNode:
        pass
    @abstractmethod
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode:
        pass
    @abstractmethod
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot:
        pass
class ColumnParameterDelegateBase[TValue](Abstract, IColumnParameterDelegate[TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetCookie(self, index: int) -> IColumnParameterCookie:
        pass
    
    @abstractmethod
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        pass
    
    @final
    def _GetParameter(self, operator: Operator, entity: Entity, index: int, primaryKeys: IReadOnlyIndexable[IDefaultColumn]) -> _IDataParameter:
        return _Parameter[object](self._GetCookie(index), operator, primaryKeys.GetAt(index)._GetEntityValue(entity)) # pyright: ignore[reportPrivateUsage]

    @final
    def __ToCondition[TNode: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator]](self, operator: Operator, entity: Entity, selector: Callable[[_IDataParameter, ConditionalOperator, _IDataParameter], TNode]) -> _IDataParameter|TNode:
        def getParameter(index: int) -> _IDataParameter:
            return self._GetParameter(operator, entity, index, primaryKeys)

        primaryKeys: ITuple[IDefaultColumn] = _GetPrimaryKeys(type(entity))
        count: int = primaryKeys.GetCount()

        if count < 1:
            raise InvalidOperationError("No primary key found.")

        parameter: _IDataParameter = getParameter(0)

        if count > 1:
            node: TNode = selector(parameter, ConditionalOperator.And, getParameter(1))
            
            if count > 2:
                self._ToForeignKeyCondition(operator, entity, primaryKeys, node, count)

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
    def ToConditionParameter(self, operator: Operator, value: TValue|Entity) -> _IDataParameter|_ValueNode:
        return self._ToConditionParameter(operator, value) if isinstance(value, Entity) else self.__ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        def toConditionNode(entity: Entity) -> _ValueNode:
            result: _IDataParameter|_ValueNode = self.ToConditionParameter(operator, entity)

            return result if isinstance(result, _ValueNode) else _ValueNode(result)
        
        return toConditionNode(value) if isinstance(value, Entity) else _ValueNode(self.__ToConditionParameter(operator, value))
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot:
        return self._ToConditionRoot(operator, value) if isinstance(value, Entity) else _ValueRoot(self.__ToConditionParameter(operator, value))
    
    @final
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter:
        return self.__ToSetConditionParameter(values)
    @final
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode:
        return _ValueNode(self.__ToSetConditionParameter(values))
    @final
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot:
        return _ValueRoot(self.__ToSetConditionParameter(values))

class ColumnParameterDelegate[TValue](ColumnParameterDelegateBase[TValue]):
    def __init__(self, cookie: IColumnParameterCookie) -> None:
        super().__init__()

        self.__cookie: IColumnParameterCookie = cookie
    
    @final
    def _GetCookie(self, index: int) -> IColumnParameterCookie:
        return self.__cookie
    
    @final
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        raise InvalidOperationError(f"Multiple primary keys found. The {foreignKeyConfig.__name__} decorator must be applied.")
class ForeignKeyParameterDelegate[TValue: Entity](ColumnParameterDelegateBase[TValue]):
    def __init__(self, cookieProvider: IColumnParameterCookieProvider) -> None:
        super().__init__()

        self.__cookieProvider: IColumnParameterCookieProvider = cookieProvider
    
    @final
    def _GetCookie(self, index: int) -> IColumnParameterCookie:
        return self.__cookieProvider.GetAt(index)
    
    @final
    def _ToForeignKeyCondition(self, operator: Operator, entity: Entity, primaryKeys: ITuple[IDefaultColumn], node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], count: int) -> None:
        def concatenate(node: ICompositeExpressionNodeBase[_IDataParameter, ConditionalOperator], index: int) -> None:
            node.GetFirst().SetNext(ConditionalOperator.And, self._GetParameter(operator, entity, index, primaryKeys))
        
        for i in range(2, count):
            concatenate(node, i)

class IEntityValueConfig[T: Entity](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetType(self) -> Type[T]:
        pass

class IColumnConfigBase(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetRole(self) -> Role:
        pass
    
    @abstractmethod
    def GetName(self) -> str|None:
        pass

class IColumnConfig(IColumnConfigBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetRole(self) -> Role:
        return Role.Null

class IPrimaryKeyConfig(IColumnConfigBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetRole(self) -> Role:
        return Role.PrimaryKey
class IEntityColumnConfig[T: Entity](IEntityValueConfig[T], IColumnConfigBase):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetRole(self) -> Role:
        return Role.ForeignKey

class IForeignKeyConfig[T: Entity](IEntityValueConfig[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetRole(self) -> Role:
        return Role.ForeignKey
    
    @abstractmethod
    def GetNames(self) -> IReadOnlyDictionary[IParameterKey, str|None]:
        pass

class EntityValueConfig[T: Entity](Abstract, IEntityValueConfig[T]):
    def __init__(self, t: Type[T]) -> None:
        super().__init__()

        self.__type: Type[T] = t
    
    @final
    def GetType(self) -> Type[T]:
        return self.__type

class ColumnConfigBase(Abstract, IColumnConfigBase):
    def __init__(self, name: str|None) -> None:
        super().__init__()

        self.__name: str|None = name
    
    @final
    def GetName(self) -> str|None:
        return self.__name

class ColumnConfig(ColumnConfigBase, IColumnConfig):
    def __init__(self, name: str|None) -> None:
        super().__init__(name)

class PrimaryKeyConfig(ColumnConfigBase, IPrimaryKeyConfig):
    def __init__(self, name: str|None) -> None:
        super().__init__(name)
class EntityColumnConfig[T: Entity](EntityValueConfig[T], IEntityColumnConfig[T]):
    def __init__(self, t: Type[T], name: str|None) -> None:
        super().__init__(t)

        self.__name: str|None = name
    
    @final
    def GetName(self) -> str|None:
        return self.__name

class ForeignKeyConfig[T: Entity](EntityValueConfig[T], IForeignKeyConfig[T]):
    def __init__(self, t: Type[T], columns: IReadOnlyDictionary[IParameterKey, str|None]) -> None:
        super().__init__(t)

        self.__columns: IReadOnlyDictionary[IParameterKey, str|None] = columns
    
    @final
    def GetNames(self) -> IReadOnlyDictionary[IParameterKey, str|None]:
        return self.__columns

class ColumnParameterAbstract(Abstract, IColumnParameterAbstract):
    @final
    class _ColumnProvider(Abstract, IColumnParameterCookie):
        def __init__(self, parameter: ColumnParameterAbstract) -> None:
            super().__init__()

            self.__parameter: ColumnParameterAbstract = parameter
        
        def _AsColumn(self, tableName: str) -> ITableColumn:
            return self.__parameter._AsColumn(tableName)
    
    def __init__(self, role: Role, name: str) -> None:
        def update(converter: IInitializableConverter[str, ITableColumn]) -> None:
            self.__column = converter

        super().__init__()
        
        self.__role: Role = role
        self.__name: str = name
        self.__column: IInitializableConverter[str, ITableColumn] = _ColumnParameterUpdater(self, update) # type: ignore[no-redef]
        self.__cookie: IColumnParameterCookie = ColumnParameterAbstract._ColumnProvider(self)
    
    @final
    def _GetCookie(self) -> IColumnParameterCookie:
        return self.__cookie
    
    @final
    def GetColumnRole(self) -> Role:
        return self.__role
    @final
    def GetColumnName(self) -> str:
        return self.__name
    
    @final
    def _SetTableName(self, tableName: str) -> None:
        self.__column.Initialize(tableName)
    
    @final
    def _AsColumn(self, tableName: str) -> ITableColumn:
        return self.__column.Convert(tableName)
class ColumnParameterBase[T: Entity](ColumnParameterAbstract, IColumnParameterBase):
    def __init__(self, func: Converter[T, object], config: IColumnConfigBase) -> None:
        def getName(name: str|None) -> str:
            return func.__name__ if name is None else name
        
        super().__init__(config.GetRole(), getName(config.GetName()))

class DefaultColumnParameter[TEntity: Entity, TValue, TConfig: IColumnConfigBase](ColumnParameterBase[TEntity], IColumnParameterBase):
    def __init__(self, func: Converter[TEntity, object], config: TConfig) -> None:
        super().__init__(func, config)

        self.__delegate: IColumnParameterDelegate[TValue] = ColumnParameterDelegate[TValue](self._GetCookie())
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode:
        return self.__delegate.ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        return self.__delegate.ToConditionNode(operator, value)
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot:
        return self.__delegate.ToConditionRoot(operator, value)
    
    @final
    def ToSetConditionParameter(self, values: IReadOnlySet[IValueObject[TValue]]) -> _IDataParameter|_ValueNode:
        return self.__delegate.ToSetConditionParameter(values)
    @final
    def ToSetConditionNode(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueNode:
        return self.__delegate.ToSetConditionNode(values)
    @final
    def ToSetConditionRoot(self, values: IReadOnlySet[IValueObject[TValue]]) -> _ValueRoot:
        return self.__delegate.ToSetConditionRoot(values)

class ColumnParameter[TEntity: Entity, TValue](DefaultColumnParameter[TEntity, TValue, IColumnConfigBase], IColumnParameter[TValue]):
    def __init__(self, func: Converter[TEntity, object], config: IColumnConfigBase) -> None:
        super().__init__(func, config)
class EntityColumnParameter[TEntity: Entity, TValue: Entity](DefaultColumnParameter[TEntity, TValue, IEntityColumnConfig[TValue]], IEntityColumnParameter[TValue]):
    def __init__(self, func: Converter[TEntity, object], config: IEntityColumnConfig[TValue]) -> None:
        super().__init__(func, config)

        self.__type: Type[TValue] = config.GetType()
    
    @final
    def GetType(self) -> Type[TValue]:
        return self.__type

class IColumnParameterCookieProvider(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetAt(self, index: int) -> IColumnParameterCookie:
        pass

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
        
        def GetAt(self, index: int) -> IColumnParameterCookie:
            return ForeignKeyParameter._CookieProvider._ColumnProvider[_TEntity, _TValue](self.__parameter, index)
    
    def __init__(self, name: str, config: IForeignKeyConfig[TValue]) -> None:
        def getNames() -> Iterable[str]:
            columnName: str|None = None

            for column in config.GetNames().AsIterable():
                yield column.GetKey().GetValue().GetColumnName() if (columnName := column.GetValue()) is None else columnName

        def update(converter: IInitializableConverter[str, ITuple[ITableColumn]]) -> None:
            self.__columns = converter
        
        super().__init__()

        self.__name: str = name
        self.__type: Type[TValue] = config.GetType()
        self.__columns: IInitializableConverter[str, ITuple[ITableColumn]] = _ForeignKeyParameterUpdater(getNames(), update) # type: ignore[no-redef]
        self.__delegate: IColumnParameterDelegate[TValue] = ForeignKeyParameterDelegate[TValue](ForeignKeyParameter._CookieProvider[TEntity, TValue](self))
    
    @final
    def GetColumnName(self) -> str:
        return self.__name
    
    @final
    def GetType(self) -> Type[TValue]:
        return self.__type
    
    @final
    def _SetTableName(self, tableName: str) -> None:
        self.__columns.Initialize(tableName)
    
    @final
    def _AsColumns(self, tableName: str) -> ITuple[ITableColumn]:
        return self.__columns.Convert(tableName)
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _IDataParameter|_ValueNode:
        return self.__delegate.ToConditionParameter(operator, value)
    @final
    def ToConditionNode(self, operator: Operator, value: TValue) -> _ValueNode:
        return self.__delegate.ToConditionNode(operator, value)
    @final
    def ToConditionRoot(self, operator: Operator, value: TValue) -> _ValueRoot:
        return self.__delegate.ToConditionRoot(operator, value)

class IColumnAbstract(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetColumnParameter(self) -> IColumnParameterAbstract:
        pass
    
    @abstractmethod
    def _GetEntityValue(self, obj: Entity) -> object:
        pass
    @abstractmethod
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        pass
class IColumnBase[T: IColumnParameterAbstract](IColumnAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetColumnParameter(self) -> T:
        pass

class IDefaultReadOnlyColumnBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](IReadOnlyProperty[TEntity, TValue, TParameter], IColumnAbstract):
    def __init__(self) -> None:
        super().__init__()
class IDefaultColumnBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](IDefaultReadOnlyColumnBase[TEntity, TValue, TParameter], IProperty[TEntity, TValue, TParameter]):
    def __init__(self) -> None:
        super().__init__()

class IDefaultColumn(IColumnBase[IColumnParameterBase]):
    def __init__(self) -> None:
        super().__init__()
class IDefaultEntityColumn(IColumnBase[IEntityColumnParameterBase]):
    def __init__(self) -> None:
        super().__init__()

class IReadOnlyColumn[TEntity: Entity, TValue](IDefaultReadOnlyColumnBase[TEntity, TValue, IColumnParameter[TValue]], IDefaultColumn):
    def __init__(self) -> None:
        super().__init__()
class IColumn[TEntity: Entity, TValue](IReadOnlyColumn[TEntity, TValue], IDefaultColumnBase[TEntity, TValue, IColumnParameter[TValue]]):
    def __init__(self) -> None:
        super().__init__()

class IEntityColumn[TEntity: Entity, TValue: Entity](IDefaultColumnBase[TEntity, TValue, IEntityColumnParameter[TValue]], IDefaultEntityColumn):
    def __init__(self) -> None:
        super().__init__()

class IDefaultForeignKey(IColumnBase[IForeignKeyParameterBase]):
    def __init__(self) -> None:
        super().__init__()
class IForeignKey[TEntity: Entity, TValue: Entity](IDefaultColumnBase[TEntity, TValue, IForeignKeyParameter[TValue]], IDefaultForeignKey):
    def __init__(self) -> None:
        super().__init__()

@final
class _ColumnConfigDecorator(Abstract):
    def __init__(self, config: IColumnConfig) -> None:
        super().__init__()

        self.__config: IColumnConfig = config
    
    def __call__[TEntity: Entity, TValue](self, func: Property[TEntity, TValue]) -> IColumn[TEntity, TValue]:
        return _Column[TEntity, TValue](func, self.__config)

class _ColumnConfigDecoratorBase[TConfig: IColumnConfigBase](Abstract):
    def __init__(self, config: TConfig) -> None:
        super().__init__()

        self.__config: TConfig = config
    
    @final
    def _GetConfig(self) -> TConfig:
        return self.__config
    
    @abstractmethod
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        pass

@final
class _ReadOnlyColumnConfigDecorator(_ColumnConfigDecoratorBase[IColumnConfig]):
    def __init__(self, config: IColumnConfig) -> None:
        super().__init__(config)
    
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        return _ReadOnlyColumn[TEntity, TValue](func, self._GetConfig())
@final
class _PrimaryKeyConfigDecorator(_ColumnConfigDecoratorBase[IPrimaryKeyConfig]):
    def __init__(self, config: IPrimaryKeyConfig) -> None:
        super().__init__(config)
    
    def __call__[TEntity: Entity, TValue](self, func: GetterBase[TEntity, TValue]) -> IReadOnlyColumn[TEntity, TValue]:
        return _PrimaryKey[TEntity, TValue](func, self._GetConfig())

class _EntityColumnConfigDecoratorBase[TValue: Entity, TConfig, TColumn](Abstract):
    def __init__(self, config: TConfig) -> None:
        super().__init__()

        self.__config: TConfig = config
    
    @final
    def _GetConfig(self) -> TConfig:
        return self.__config
    
    @abstractmethod
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> TColumn:
        pass

@final
class _EntityColumnConfigDecorator[TValue: Entity](_EntityColumnConfigDecoratorBase[TValue, IEntityColumnConfig[TValue], IDefaultEntityColumn]):
    def __init__(self, config: IEntityColumnConfig[TValue]) -> None:
        super().__init__(config)
    
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> IEntityColumn[TEntity, TValue]:
        return _EntityColumn[TEntity, TValue](func, self._GetConfig())
@final
class _ForeignKeyConfigDecorator[TValue: Entity](_EntityColumnConfigDecoratorBase[TValue, IForeignKeyConfig[TValue], IDefaultForeignKey]):
    def __init__(self, config: IForeignKeyConfig[TValue]) -> None:
        super().__init__(config)
    
    def __call__[TEntity: Entity](self, func: Property[TEntity, TValue]) -> IForeignKey[TEntity, TValue]:
        return _ForeignKey[TEntity, TValue](func, self._GetConfig())

def readOnlyColumnConfig(name: str|None = None) -> _ReadOnlyColumnConfigDecorator:
    return _ReadOnlyColumnConfigDecorator(ColumnConfig(name))
def columnConfig(name: str|None = None) -> _ColumnConfigDecorator:
    return _ColumnConfigDecorator(ColumnConfig(name))

def primaryKeyConfig(name: str|None = None) -> _PrimaryKeyConfigDecorator:
    return _PrimaryKeyConfigDecorator(PrimaryKeyConfig(name))
def entityColumnConfig[T: Entity](t: Type[T], name: str|None = None) -> _EntityColumnConfigDecorator[T]:
    return _EntityColumnConfigDecorator[T](EntityColumnConfig[T](t, name))

def foreignKeyConfiguration[T: Entity](t: Type[T], columns: IReadOnlyDictionary[IParameterKey, str|None]) -> _ForeignKeyConfigDecorator[T]:
    return _ForeignKeyConfigDecorator[T](ForeignKeyConfig[T](t, columns))
def foreignKeyConfig[T: Entity](t: Type[T], columns: Iterable[tuple[IColumnParameterAbstract, str|None]]) -> _ForeignKeyConfigDecorator[T]:
    return foreignKeyConfiguration(t, CreateDictionary(dict[IParameterKey, str|None](Select(columns, lambda column: (ParameterKey(column[0]), column[1])))).AsReadOnly())

class ICookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsReady(self) -> bool:
        pass
    
    @abstractmethod
    def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T:
        pass
    @abstractmethod
    def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None:
        pass

def _GetCookie(obj: Entity) -> ICookie:
    return obj._GetCookie() # pyright: ignore[reportPrivateUsage]

class _ColumnDecoratorBase[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract, TProperty](Abstract, IFunctionProvider[TEntity, TValue, TProperty]):
    def __init__(self, parameter: TParameter, func: TProperty, setter: SetterBase[Entity, object]) -> None:
        super().__init__()
        
        _func: GetterBase[TEntity, TValue] = self._AsFunction(func)

        self.__parameter: TParameter = parameter
        self.__getter: GetterBase[Entity, object] = lambda entity: _func(cast(TEntity, entity))
        self.__setter: SetterBase[Entity, object] = setter
    
    @final
    def GetColumnParameter(self) -> TParameter:
        return self.__parameter
    
    @final
    def GetEntityValue(self, obj: Entity, name: str) -> object:
        return _GetCookie(obj).GetValue(name, self.__getter)
    @final
    def GetValue(self, obj: TEntity|None, name: str) -> TValue|TParameter:
        return self.GetColumnParameter() if obj is None else cast(TValue, _GetCookie(obj).GetValue(name, self.__getter))
    
    def SetValue(self, obj: Entity, name: str, value: object) -> None:
        _GetCookie(obj).SetValue(name, self.__setter, value)

@final
class _ReadOnlyColumnDecorator[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](_ColumnDecoratorBase[TEntity, TValue, TParameter, GetterBase[TEntity, TValue]], IGetterProvider[TEntity, TValue]):
    def __init__(self, parameter: TParameter, func: GetterBase[TEntity, TValue]) -> None:
        def setValue(entity: Entity) -> IMethodBase[object]:
            raise InvalidOperationError("Cannot update read-only column or primary key.")

        super().__init__(parameter, func, setValue)
@final
class _ColumnDecorator[TEntity: Entity, TValue, TParameter: IColumnParameterAbstract](_ColumnDecoratorBase[TEntity, TValue, TParameter, Property[TEntity, TValue]], IPropertyProvider[TEntity, TValue]):
    def __init__(self, parameter: TParameter, func: Property[TEntity, TValue]) -> None:
        super().__init__(parameter, func, lambda entity: cast(IMethodBase[object], func(cast(TEntity, entity)).AsMethod()))
    
def _GetName[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](column: _IColumn[TEntity, TValue, TDecorator, TConfig, TParameter, TProperty]) -> str:
    return column._GetDecoratorAsInterface().GetColumnParameter().GetColumnName() # pyright: ignore[reportPrivateUsage]

class _IColumn[TEntity: Entity, TValue, TDecorator, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase, TProperty](IReadOnlyProperty[TEntity, TValue, TParameter], IColumnAbstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsDecorator(self, decorator: TDecorator) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, TProperty]:
        pass
    
    @abstractmethod
    def _CreateParameter(self, func: TProperty, config: TConfig) -> TParameter:
        pass
    
    @abstractmethod
    def _GetDecorator(self) -> TDecorator:
        pass
    @final
    def _GetDecoratorAsInterface(self) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, TProperty]:
        return self._AsDecorator(self._GetDecorator())
    
    @final
    def GetColumnParameter(self) -> TParameter:
        return self._GetDecoratorAsInterface().GetColumnParameter()
    
    @final
    def _GetValue(self, obj: TEntity|None) -> TValue|TParameter:
        return self._GetDecoratorAsInterface().GetValue(obj, _GetName(self))
    @final
    def _GetEntityValue(self, obj: Entity) -> object:
        return self._GetDecoratorAsInterface().GetEntityValue(obj, _GetName(self))

class _ReadOnlyColumnBase[TEntity: Entity, TValue, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase](ReadOnlyPropertyDecorator[TEntity, TValue, TParameter], _IColumn[TEntity, TValue, _ReadOnlyColumnDecorator[TEntity, TValue, TParameter], TConfig, TParameter, GetterBase[TEntity, TValue]]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: TConfig) -> None:
        super().__init__(func)

        self.__decorator: _ReadOnlyColumnDecorator[TEntity, TValue, TParameter] = _ReadOnlyColumnDecorator[TEntity, TValue, TParameter](self._CreateParameter(func, config), func)
    
    @final
    def _AsDecorator(self, decorator: _ReadOnlyColumnDecorator[TEntity, TValue, TParameter]) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, GetterBase[TEntity, TValue]]:
        return decorator
    
    @final
    def _GetDecorator(self) -> _ReadOnlyColumnDecorator[TEntity, TValue, TParameter]:
        return self.__decorator
    
    @final
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|TParameter:
        return self._GetValue(obj)
    
    @final
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        self._GetDecorator().SetValue(obj, _GetName(self), value)
class _ColumnBase[TEntity: Entity, TValue, TConfig: IColumnConfigBase, TParameter: IColumnParameterBase](PropertyDecorator[TEntity, TValue, TParameter], _IColumn[TEntity, TValue, _ColumnDecorator[TEntity, TValue, TParameter], TConfig, TParameter, Property[TEntity, TValue]]):
    def __init__(self, func: Property[TEntity, TValue], config: TConfig) -> None:
        super().__init__(func)

        self.__decorator: _ColumnDecorator[TEntity, TValue, TParameter] = _ColumnDecorator[TEntity, TValue, TParameter](self._CreateParameter(func, config), self._GetFunc())
    
    @final
    def _AsDecorator(self, decorator: _ColumnDecorator[TEntity, TValue, TParameter]) -> _ColumnDecoratorBase[TEntity, TValue, TParameter, Property[TEntity, TValue]]:
        return decorator
    
    @final
    def _GetDecorator(self) -> _ColumnDecorator[TEntity, TValue, TParameter]:
        return self.__decorator
    
    @final
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|TParameter:
        return self._GetValue(obj)
    
    @final
    def Set(self, obj: TEntity, value: TValue, objtype: type|None = None) -> None:
        self._GetDecorator().SetValue(obj, _GetName(self), value)
    @final
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        self._GetDecorator().SetValue(obj, _GetName(self), value)

@final
class _ReadOnlyColumn[TEntity: Entity, TValue](_ReadOnlyColumnBase[TEntity, TValue, IColumnConfig, IColumnParameter[TValue]], IReadOnlyColumn[TEntity, TValue]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: IColumnConfig) -> None:
        super().__init__(func, config)
    
    def _CreateParameter(self, func: GetterBase[TEntity, TValue], config: IColumnConfig) -> IColumnParameter[TValue]:
        return ColumnParameter[TEntity, TValue](func, config)
@final
class _Column[TEntity: Entity, TValue](_ColumnBase[TEntity, TValue, IColumnConfig, IColumnParameter[TValue]], IColumn[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IColumnConfig) -> None:
        super().__init__(func, config)
    
    def _CreateParameter(self, func: Property[TEntity, TValue], config: IColumnConfig) -> IColumnParameter[TValue]:
        return ColumnParameter[TEntity, TValue](func, config)

@final
class _PrimaryKey[TEntity: Entity, TValue](_ReadOnlyColumnBase[TEntity, TValue, IPrimaryKeyConfig, IColumnParameter[TValue]], IReadOnlyColumn[TEntity, TValue]):
    def __init__(self, func: GetterBase[TEntity, TValue], config: IPrimaryKeyConfig) -> None:
        super().__init__(func, config)
    
    def _CreateParameter(self, func: GetterBase[TEntity, TValue], config: IPrimaryKeyConfig) -> IColumnParameter[TValue]:
        return ColumnParameter[TEntity, TValue](func, config)
@final
class _EntityColumn[TEntity: Entity, TValue: Entity](_ColumnBase[TEntity, TValue, IEntityColumnConfig[TValue], IEntityColumnParameter[TValue]], IEntityColumn[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IEntityColumnConfig[TValue]) -> None:
        super().__init__(func, config)
    
    def _CreateParameter(self, func: Property[TEntity, TValue], config: IEntityColumnConfig[TValue]) -> IEntityColumnParameter[TValue]:
        return EntityColumnParameter[TEntity, TValue](func, config)

@final
class _ForeignKey[TEntity: Entity, TValue: Entity](PropertyDecorator[TEntity, TValue, IForeignKeyParameter[TValue]], IForeignKey[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IForeignKeyConfig[TValue]) -> None:
        super().__init__(func)

        self.__decorator: _ColumnDecorator[TEntity, TValue, IForeignKeyParameter[TValue]] = _ColumnDecorator[TEntity, TValue, IForeignKeyParameter[TValue]](ForeignKeyParameter[TEntity, TValue](func.__name__, config), func)
    
    def __GetName(self) -> str:
        return self.__decorator.GetColumnParameter().GetColumnName()
    
    def GetColumnParameter(self) -> IForeignKeyParameter[TValue]:
        return self.__decorator.GetColumnParameter()
    
    def _GetEntityValue(self, obj: Entity) -> object:
        return self.__decorator.GetEntityValue(obj, self.__GetName())
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        self.__decorator.SetValue(obj, self.__GetName(), value)
    
    def Get(self, obj: TEntity|None, objtype: type|None = None) -> TValue|IForeignKeyParameter[TValue]:
        return self.__decorator.GetValue(obj, self.__GetName())
    def Set(self, obj: TEntity, value: TValue) -> None:
        self.__decorator.SetValue(obj, self.__GetName(), value)

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
        def checkRole(column: IColumnAbstract, role: Role) -> bool:
            return column.GetColumnParameter().GetColumnRole() == role
        def getPredicate(role: Role) -> Predicate[IColumnAbstract]:
            return lambda column: checkRole(column, role)
        def concatenate(*columns: IEnumerable[IColumnAbstract]) -> Iterable[IColumnAbstract]:
            return ConcatenateIterables(Select(columns, lambda items: items.AsIterable()))
        
        def createTuple[T](t: Type[T], role: Role, columns: IIterator[IColumnAbstract]) -> ITuple[T]:
            return CreateTuple(WhereOfType(t, columns.Include(getPredicate(role))))

        super().__init__()

        _columns: IList[IColumnAbstract] = CreateList(columns)
        __columns: IIterator[IColumnAbstract] = _columns.AsGenerator()

        # The order of parsing is mandatory to get consistent set.

        self.__primaryKeys: ITuple[IDefaultColumn] = createTuple(IDefaultColumn, Role.PrimaryKey, __columns) # type: ignore[type-abstract]
        self.__foreignKeys: ITuple[IDefaultForeignKey] = CreateTuple(__columns.WhereOfType(IDefaultForeignKey)) # type: ignore[type-abstract]
        self.__entityColumns: ITuple[IDefaultEntityColumn] = createTuple(IDefaultEntityColumn, Role.ForeignKey, __columns) # type: ignore[type-abstract]
        self.__columns: ITuple[IDefaultColumn] = CreateTuple(WhereOfType(IDefaultColumn, _columns.AsQueuedGenerator())) # type: ignore[type-abstract]

        self.__allColumns: Iterable[IColumnAbstract] = concatenate(self.__primaryKeys, self.__columns, self.__entityColumns, self.__foreignKeys)
    
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
    def _GetValue(self) -> _Columns:
        return _Columns(WhereOfType(IColumnAbstract, self.__type.__dict__.values())) # type: ignore[type-abstract]

class IEntityKey[T: IItem](IItemObject[T, 'IEntityKey[T]|T'], IEnumerable[IValueItem]):
    def __init__(self) -> None:
        super().__init__()

class EntityKeyBase[T: IItem](Abstract, IEntityKey[T]):
    def __init__(self, key: T, enumerable: IEnumerable[IValueItem]) -> None:
        super().__init__()

        self.__key: T = key
        self.__enumerable: IEnumerable[IValueItem] = enumerable
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IValueItem]|None:
        return self.__enumerable.TryGetEnumerator()
    
    @final
    def AsIterable(self) -> Iterable[IValueItem]:
        return self.__enumerable.AsIterable()
    
    @final
    def GetValue(self) -> T:
        return self.__key
    @final
    def GetUnderlyingValue(self) -> T:
        return self.GetValue()
    
    def Equals(self, item: T|IEntityKey[T]|object) -> bool:
        return self.GetValue().Equals(item.GetUnderlyingValue() if isinstance(item, IEntityKey) else item)
    
    def Hash(self) -> int:
        return self.GetValue().Hash()
    
    def ToString(self) -> str:
        return self.GetValue().ToString()
class EntityKey[T: IValueItem](EntityKeyBase[T], IEntityKey[T]):
    @final
    class _Enumerable[_T: IValueItem](Enumerable[_T]):
        @final
        class _Enumerator[__T: IValueItem](EnumeratorBase[__T]):
            def __init__(self, key: IEntityKey[__T]) -> None:
                super().__init__()

                self.__key: IEntityKey[__T] = key
                self.__canMoveNext: bool|None = True
            
            def IsResetSupported(self) -> bool:
                return True
            
            def _GetCurrent(self) -> __T:
                if self.__canMoveNext is None:
                    return self.__key.GetValue()
                
                raise GetEnumeratorInactiveError()
            
            def _MoveNextOverride(self) -> bool:
                canMoveNext: bool|None = self.__canMoveNext

                if canMoveNext is True:
                    self.__canMoveNext = None

                    return True
                
                if canMoveNext is None:
                    self.__canMoveNext = False

                return False
            
            def _ResetOverride(self) -> bool:
                self.__canMoveNext = True
                
                return True
            
            def _OnStopped(self) -> None:
                pass
        
        def __init__(self, key: EntityKey[_T]) -> None:
            super().__init__()

            self.__key: IEntityKey[_T] = key
        
        def TryGetEnumerator(self) -> IEnumerator[_T]|None:
            return EntityKey[_T]._Enumerable._Enumerator(self.__key)
    
    def __init__(self, key: T) -> None:
        super().__init__(key, EntityKey[T]._Enumerable(self))
class CompositeEntityKey[T: IValueItem](EntityKeyBase[IHashableTuple[T]], IEntityKey[IHashableTuple[T]]):
    def __init__(self, keys: IHashableTuple[T]) -> None:
        super().__init__(keys, self.GetValue())

def _SetEntityValue(obj: Entity, column: IColumnAbstract, value: object) -> None:
    column._SetEntityValue(obj, value) # pyright: ignore[reportPrivateUsage]

def __ProcessColumns[TColumn: IColumnAbstract](obj: Entity, columns: Iterable[TColumn], row: Iterable[object], converter: Converter[tuple[TColumn, object], object]) -> None:
    def setValue(args: tuple[TColumn, object]) -> None:
        _SetEntityValue(obj, args[0], converter(args))

    DoForEachItem(zip(columns, row), setValue)
def _ProcessColumns[TColumn: IColumnAbstract](obj: Entity, row: Iterable[object], columns: Iterable[TColumn]) -> None:
    __ProcessColumns(obj, columns, row, lambda args: args[1])

class IEntityMapper[T: Entity](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsKey(self) -> IType[T]:
        pass

    @abstractmethod
    def GetKey(self, keys: ITuple[object]) -> IEntityKey[IItem]:
        pass
    
    @abstractmethod
    def GetEntity(self, key: IEntityKey[IItem]) -> T:
        pass
    @final
    def GetEntityFromKeys(self, keys: ITuple[object]) -> T:
        return self.GetEntity(self.GetKey(keys))
class EntityMapper[T: Entity](Abstract, IEntityMapper[T]):
    def __init__(self, t: Type[T]) -> None:
        super().__init__()

        self.__type: IType[T] = TypeObject[T](t)
        self.__items: IDictionary[IEntityKey[IItem], T] = Dictionary[IEntityKey[IItem], T]()
    
    @final
    def _GetItems(self) -> IDictionary[IEntityKey[IItem], T]:
        return self.__items
    
    @final
    def AsKey(self) -> IType[T]:
        return self.__type

    @final
    def GetKey(self, keys: ITuple[object]) -> IEntityKey[IItem]:
        def getKey(key: object) -> IValueItem:
            return Map(key)
        
        t: Type[T] = self.__type.GetValue()
        count: int = _GetPrimaryKeys(t).GetCount()

        if keys.GetCount() == count:
            if count < 1:
                raise InvalidOperationError("No primary key found.")
            
            return CompositeEntityKey[IValueItem](CreateHashableTuple(Select(keys.AsIterable(), getKey))) if count > 1 else EntityKey[IValueItem](getKey(keys.GetAt(0)))

        raise ValueError(f"The given key collection's length does not match the primary keys length of {t}.")
    
    @final
    def GetEntity(self, key: IEntityKey[IItem]) -> T:
        entity: T|None = self._GetItems().TryGetValue(key).TryGetValue()

        if entity is None:
            t: Type[T] = self.AsKey().GetValue()

            self._GetItems().Add(key, entity := object.__new__(t))
            
            entity._InitCookie() # pyright: ignore[reportPrivateUsage]

            _ProcessColumns(entity, Select(key.AsIterable(), lambda key: key.GetValue()), _GetPrimaryKeys(t).AsIterable())

        return entity

class Entity(Abstract, IDisposable):
    class _Cookie(Abstract, ICookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__()

            self.__entity: Entity = entity
        
        @abstractmethod
        def Seal(self) -> None:
            pass
        
        @final
        def _GetEntity(self) -> Entity:
            return self.__entity
    
    @final
    class _AppCookie(_Cookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__(entity)

        @final
        def IsReady(self) -> bool:
            return True
        
        def Seal(self) -> None:
            pass
        
        def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T:
            return func(self._GetEntity()).GetValue()
        def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None:
            return func(self._GetEntity()).SetValue(value)
    @final
    class _DBCookie(_Cookie):
        def __init__(self, entity: Entity) -> None:
            super().__init__(entity)

            self.__isReady: bool = False
            self.__values: IDictionary[IString, Any] = Dictionary[IString, Any]()
        
        def IsReady(self) -> bool:
            return self.__isReady
        
        def Seal(self) -> None:
            self.__isReady = True
        
        def GetValue[T](self, name: str, func: GetterBase[Entity, T]) -> T:
            return cast(T, self.__values.TryGetValue(String(name)).GetValue())
        def SetValue[T](self, name: str, func: SetterBase[Entity, T], value: T) -> None:
            self.__values.AddOrUpdate(String(name), value)
    
    __columns: IFunction[_Columns]

    def __init_subclass__(cls, **kwargs: object) -> None:
        def update(func: IFunction[_Columns]) -> None:
            cls.__columns = func
        
        super().__init_subclass__(**kwargs)
        
        cls.__columns = _EntityUpdater(cls, update)

    @classmethod
    @final
    def _GetColumns(cls) -> _Columns:
        return cls.__columns.GetValue()
    
    def __init__(self) -> None:
        super().__init__()

        self.__cookie: Entity._Cookie = Entity._AppCookie(self)
    
    @final
    def _InitCookie(self) -> None:
        self.__cookie = Entity._DBCookie(self)
    
    @final
    def _GetCookie(self) -> ICookie:
        return self.__cookie
    
    def _InitializeOverride(self) -> None:
        pass
    
    @final
    def IsReady(self) -> bool:
        return self._GetCookie().IsReady()
    
    @final
    def Initialize(self) -> None:
        self._InitializeOverride()

        self.__cookie.Seal() # TODO: Should be called from protected variant

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

class EntityCollection[T: Entity](Abstract):
    def __init__(self, context: DataContextBase) -> None:
        super().__init__()

        self.__context: DataContextBase = context
    
    @abstractmethod
    def _GetType(self) -> Type[T]:
        pass

    @final
    def __Iterate(self, data: _SelectionQueryData, query: ISelectionQuery) -> IEnumerable[T]:
        def iterate(items: ISelectionQueryExecutionResult) -> Generator[T]:
            def createEntity(row: Iterator[object]) -> T:
                def __getEntity[_T: Entity](t: Type[_T], values: ITuple[object]) -> _T:
                    return self.__context._GetMapper(t).GetEntityFromKeys(values) # pyright: ignore[reportPrivateUsage]
                def _getEntity[_T: Entity](t: Type[_T], primaryKeys: Iterable[IDefaultColumn]) -> _T:
                    return __getEntity(t, CreateTuple(Select(primaryKeys, lambda _: next(row)))) # pyright: ignore[reportPrivateUsage]
                def getEntity[_T: Entity](t: Type[_T]) -> _T:
                    return _getEntity(t, _GetPrimaryKeys(t).AsIterable())

                obj: T = _getEntity(self._GetType(), data.GetPrimaryKeys())

                if obj.IsReady():
                    return obj
                
                _ProcessColumns(obj, row, data.GetColumns())
                __ProcessColumns(obj, data.GetEntityColumns(), row, lambda args: __getEntity(args[0].GetColumnParameter().GetType(), MakeTuple(args[1])))

                for fk in data.GetForeignKeys():
                    _SetEntityValue(obj, fk, getEntity(fk.GetColumnParameter().GetType()))

                obj.Initialize()

                return obj
            
            for row in items.AsIterable():
                yield createEntity(iter(row))

        items: ISelectionQueryExecutionResult|None = query.Execute()

        return GetEmptyEnumerable() if items is None else IteratorProvider[T](lambda: iterate(items))
    
    @final
    def __GetDefaultTableName(self) -> str:
        return self._GetType().__name__
    
    @final
    def __GetSelectionQuery(self) -> tuple[_SelectionQueryData, ISelectionQuery]:
        def getDefaultTableName() -> str:
            return self.__GetDefaultTableName()

        data: _SelectionQueryData = _SelectionQueryData(_GetColumns(self._GetType()))

        return data, self.__context._GetConnection().GetQueryFactory().GetSelectionQuery( # pyright: ignore[reportPrivateUsage]
            TableParameterSet.CreateFromNames(String(getDefaultTableName())),
            CreateColumnParameterSet(
                ConcatenateValues(
                    ConcatenateIterables(Select((data.GetPrimaryKeys(), data.GetColumns(), data.GetEntityColumns()), lambda columns: Select(columns, lambda column: column.GetColumnParameter()._AsColumn(getDefaultTableName())))), # pyright: ignore[reportPrivateUsage]
                    ConcatenateIterables(Select(data.GetForeignKeys(), lambda  column: column.GetColumnParameter()._AsColumns(getDefaultTableName()).AsIterable()))))) # pyright: ignore[reportPrivateUsage]
    
    @final
    def Select(self) -> IEnumerable[T]:
        return self.__Iterate(*self.__GetSelectionQuery())

    @final
    def Where(self, conditions: _IRoot) -> IEnumerable[T]:
        data, query = self.__GetSelectionQuery()

        query.SetConditions(TryCreateConditionSetFromConditions(_Set(conditions, self.__GetDefaultTableName())))
        # Select(conditions, lambda condition: CreateKeyValuePair(asColumn(condition.GetKey()), condition.GetValue()))
        
        return self.__Iterate(data, query)

class DataContextBase(Abstract):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IDictionary[IType[Entity], IEntityMapper[Entity]] = Dictionary[IType[Entity], IEntityMapper[Entity]]()

    @abstractmethod
    def _GetConnection(self) -> IConnection:
        pass

    @final
    def _GetMapper[T: Entity](self, t: Type[T]) -> IEntityMapper[T]:
        _t: IType[T] = TypeObject[T](t)
        mapper: IEntityMapper[T]|None = cast(IEntityMapper[T]|None, self.__items.TryGetValue(_t).TryGetValue())

        if mapper is None:
            self.__items.Add(_t, mapper := EntityMapper[T](t))
        
        return mapper
class DataContext(DataContextBase):
    def __init__(self, connection: IConnection) -> None:
        super().__init__()

        self.__connection: IConnection = connection

    @final
    def _GetConnection(self) -> IConnection:
        return self.__connection