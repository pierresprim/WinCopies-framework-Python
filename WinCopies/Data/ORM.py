from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import final, overload, Any, Type, cast

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator, EnumerationOrder
from WinCopies.Collections.Abstraction.Collection import Dictionary, CreateTuple
from WinCopies.Collections.Enumeration import IEnumerable, IEnumerator, IteratorProvider, GetEmptyEnumerable, AsEnumerator
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler, IRecursiveStackedEnumerationHandler, RecursivelyIterableProvider, CreateRecursivelyIterableProvider
from WinCopies.Collections.Enumeration.Recursive.Enumerable import RecursiveEnumerator, StackedRecursiveEnumerator
from WinCopies.Collections.Expression import IConnector, ICompositeExpression, ICompositeExpressionNode, ICompositeExpressionRoot, CompositeExpressionValueNode, CompositeExpressionNode, CompositeExpressionValueRoot, CompositeExpressionRoot
from WinCopies.Collections.Extensions import ITuple, IDictionary
from WinCopies.Collections.Iteration import Select, WhereOfType
from WinCopies.Typing import IDisposable
from WinCopies.Typing.Delegate import IFunction, Method, Converter, Selector, IInitializableConverter, IStruct, ValueFunction, ValueFunctionUpdater, ValueConverterUpdater
from WinCopies.Typing.Object import IString, String
from WinCopies.Typing.Pairing import IKeyValuePair, CreateKeyValuePair



from WinCopies.Data import Operator, ConditionalOperator, IOperandValue, ITableColumn, Operand
from WinCopies.Data.Abstract import IConnection
from WinCopies.Data.Parameter import IParameter, FieldParameter
from WinCopies.Data.Query import ISelectionQueryExecutionResult
from WinCopies.Data.Set import IFieldConditionRecursivelyEnumerable, IFieldParameterSetItem
from WinCopies.Data.Set.Extensions import TableParameterSet, CreateColumnParameterSet, TryCreateConditionSetFromConditions

type Property[TEntity, TValue] = Converter[TEntity, IStruct[TValue]]

class IFunctionDecorator[TEntity, TValue](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def __call__(self, obj: TEntity, *args: object, **kwargs: object) -> TValue:
        pass

class _FunctionDecorator[TEntity, TValue](Abstract, IFunctionDecorator[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue]) -> None:
        super().__init__()

        self.__func: Property[TEntity, TValue] = func
    
    @final
    def _GetFunc(self) -> Property[TEntity, TValue]:
        return self.__func
    
    def _Invoke(self, obj: TEntity, *args: object, **kwargs: object) -> TValue:
        return self.__func(obj, *args, **kwargs).GetValue()
    
    @final
    def __call__(self, obj: TEntity, *args: object, **kwargs: object) -> TValue:
        return self._Invoke(obj, *args, **kwargs)
class FunctionDecorator[TEntity, TValue](_FunctionDecorator[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue]) -> None:
        super().__init__(func)

@final
class _TableColumn(Abstract, ITableColumn):
    def __init__(self, parameter: ColumnParameterAbstract, tableName: str) -> None:
        super().__init__()

        self.__parameter: ColumnParameterAbstract = parameter
        self.__tableName: str = tableName
    
    def GetColumnName(self) -> str:
        return self.__parameter.GetColumnName()
    
    def GetTableName(self) -> str:
        return self.__tableName

@final
class _ColumnParameterUpdater(ValueConverterUpdater[str, ITableColumn]):
    def __init__(self, parameter: ColumnParameterAbstract, updater: Method[IInitializableConverter[str, ITableColumn]]) -> None:
        super().__init__(updater)

        self.__parameter: ColumnParameterAbstract = parameter
    
    def ConvertValue(self, value: str) -> ITableColumn:
        return _TableColumn(self.__parameter, value)

class _IColumnParameterCookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsColumn(self, tableName: str) -> ITableColumn:
        pass

@final
class _Parameter[T](Abstract, IKeyValuePair[_IColumnParameterCookie, IParameter[IOperandValue]|None]):
    def __init__(self, cookie: _IColumnParameterCookie, operator: Operator, value: T) -> None:
        super().__init__()

        self.__columnParameter: _IColumnParameterCookie = cookie
        self.__parameter: IParameter[IOperandValue] = FieldParameter[T](Operand[T](operator, value))
    
    def IsKeyValuePair(self) -> bool:
        return False
    
    def GetKey(self) -> _IColumnParameterCookie:
        return self.__columnParameter
    def GetValue(self) -> IParameter[IOperandValue]|None:
        return self.__parameter

class _INode(ICompositeExpressionNode[_Parameter[object], ConditionalOperator]):
    def __init__(self) -> None:
        super().__init__()
class _IRoot(ICompositeExpressionRoot[_Parameter[object], ConditionalOperator]):
    def __init__(self) -> None:
        super().__init__()

@final
class _ValueNode(CompositeExpressionValueNode[_Parameter[object], ConditionalOperator], _INode):
    def __init__(self, parameter: _Parameter[object]) -> None:
        super().__init__(parameter)
@final
class _Node(CompositeExpressionNode[_Parameter[object], ConditionalOperator], _INode):
    def __init__(self, node: _INode) -> None:
        super().__init__(node)

@final
class _ValueRoot(CompositeExpressionValueRoot[_Parameter[object], ConditionalOperator], _IRoot):
    def __init__(self, parameter: _Parameter[object]) -> None:
        super().__init__(parameter)
@final
class _Root(CompositeExpressionRoot[_Parameter[object], ConditionalOperator], _IRoot):
    def __init__(self, x: _INode) -> None:
        super().__init__(x)

type ValueNode = _ValueNode
type Node = _Node

type ValueRoot = _ValueRoot
type Root = _Root

def Concatenate(x: _Parameter[object], operator: ConditionalOperator, y: _Parameter[object]) -> _ValueNode:
    node: _ValueNode = _ValueNode(x)

    node.GetFirst().SetNext(operator, y)

    return node
def ConcatenateNode(x: _INode, operator: ConditionalOperator, y: _Parameter[object]) -> _Node:
    node: _Node = _Node(x)

    node.GetFirst().SetNext(operator, y)

    return node
def ConcatenateNodes(x: _INode, operator: ConditionalOperator, y: _INode) -> _Node:
    node: _Node = _Node(x)

    node.GetFirst().SetNextExpression(operator, y)

    return node

def ConcatenateAsRoot(x: _Parameter[object], operator: ConditionalOperator, y: _Parameter[object]) -> _ValueRoot:
    root: _ValueRoot = _ValueRoot(x)

    root.GetFirst().SetNext(operator, y)

    return root
def ConcatenateNodeAsRoot(x: _INode, operator: ConditionalOperator, y: _Parameter[object]) -> _Root:
    root: _Root = _Root(x)

    root.GetFirst().SetNext(operator, y)

    return root
def ConcatenateNodesAsRoot(x: _INode, operator: ConditionalOperator, y: _INode) -> _Root:
    root: _Root = _Root(x)

    root.GetFirst().SetNextExpression(operator, y)

    return root

def _TryGetConnector(connector: IConnector[_Parameter[object], ConditionalOperator]|None) -> ConditionalOperator|None:
    return None if connector is None else connector.GetConnector()

@final
class _Expression(Abstract, IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]):
    def __init__(self, expression: ICompositeExpression[_Parameter[object], ConditionalOperator], tableName: str) -> None:
        super().__init__()

        self.__expression: ICompositeExpression[_Parameter[object], ConditionalOperator] = expression
        self.__tableName: str = tableName
    
    def TryGetFieldParameter(self) -> IKeyValuePair[ITableColumn, IParameter[IOperandValue]|None]|None:
        parameter: _Parameter[object]|None = self.__expression.TryGetValue().TryGetValue()

        return None if parameter is None else CreateKeyValuePair(parameter.GetKey()._AsColumn(self.__tableName), parameter.GetValue()) # pyright: ignore[reportPrivateUsage]
    
    def TryGetPreviousOperator(self) -> ConditionalOperator|None:
        return _TryGetConnector(self.__expression.GetPrevious())
    def TryGetNextOperator(self) -> ConditionalOperator|None:
        return _TryGetConnector(self.__expression.GetNext())
    
    def TryGetItems(self) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None:
        expression: ICompositeExpressionNode[_Parameter[object], ConditionalOperator]|None = self.__expression.TryGetItems()

        return None if expression is None else IteratorProvider[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]](lambda: Select(expression.AsIterable(), lambda expression: _Expression(expression, self.__tableName)))

def _GetEnumerable(enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
    items: IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = enumerationItems.TryGetItems()

    return GetEmptyEnumerable() if items is None else items

class _RecursiveEnumerator(RecursiveEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]):
    def __init__(self, enumerator: IEnumerator[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]], handler: IRecursiveEnumerationHandler[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]|None = None) -> None:
        super().__init__(enumerator, handler)
    
    @final
    def _GetEnumerationItems(self, enumerationItems: IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]) -> IEnumerable[IFieldParameterSetItem[ITableColumn, IParameter[IOperandValue]]]:
        return _GetEnumerable(enumerationItems)
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

class ColumnParameterAbstract(Abstract):
    @final
    class _ColumnProvider(Abstract, _IColumnParameterCookie):
        def __init__(self, parameter: ColumnParameterAbstract) -> None:
            super().__init__()

            self.__parameter: ColumnParameterAbstract = parameter
        
        def _AsColumn(self, tableName: str) -> ITableColumn:
            return self.__parameter._AsColumn(tableName)
    
    def __init__(self, name: str) -> None:
        def update(converter: IInitializableConverter[str, ITableColumn]) -> None:
            self.__column = converter

        super().__init__()
        
        self.__name: str = name
        self.__column: IInitializableConverter[str, ITableColumn] = _ColumnParameterUpdater(self, update) # type: ignore[no-redef]
        self.__cookie: _IColumnParameterCookie = ColumnParameterAbstract._ColumnProvider(self)
    
    @final
    def _GetCookie(self) -> _IColumnParameterCookie:
        return self.__cookie
    
    @final
    def GetColumnName(self) -> str:
        return self.__name
    
    @final
    def _SetTableName(self, tableName: str) -> None:
        self.__column.Initialize(tableName)
    
    @final
    def _AsColumn(self, tableName: str) -> ITableColumn:
        return self.__column.Convert(tableName)
class ColumnParameterBase[T: Entity](ColumnParameterAbstract):
    def __init__(self, func: Converter[T, object], config: IColumnConfig) -> None:
        def getName(name: str|None) -> str:
            return func.__name__ if name is None else name
        
        super().__init__(getName(config.GetName()))
class ColumnParameter[TEntity: Entity, TValue](ColumnParameterBase[TEntity]):
    def __init__(self, func: Converter[TEntity, object], config: IColumnConfig) -> None:
        super().__init__(func, config)
    
    @final
    def ToConditionParameter(self, operator: Operator, value: TValue) -> _Parameter[TValue]:
        if isinstance(value, Entity):
            pass

        return _Parameter(self._GetCookie(), operator, value)

class IColumnBase(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetColumnParameter(self) -> ColumnParameterBase[Entity]:
        pass
    
    @abstractmethod
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        pass
class IColumn[TEntity: Entity, TValue](IFunctionDecorator[TEntity, TValue], IColumnBase):
    def __init__(self) -> None:
        super().__init__()
    
    @overload
    def __get__(self, obj: TEntity, objtype: type|None = None) -> TValue:
        ...
    @overload
    def __get__(self, obj: None, objtype: type|None = None) -> ColumnParameter[TEntity, TValue]:
        ...
    
    @abstractmethod
    def __get__(self, obj: TEntity|None, objtype: type|None = None) -> TValue|ColumnParameter[TEntity, TValue]:
        pass
    @abstractmethod
    def __set__(self, instance: TEntity, value: TValue) -> None:
        pass

class IColumnConfig(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsPrimaryKey(self) -> bool:
        pass
    @abstractmethod
    def GetName(self) -> str|None:
        pass
class ColumnConfig(Abstract, IColumnConfig):
    def __init__(self, primaryKey: bool = False, name: str|None = None) -> None:
        super().__init__()

        self.__primaryKey: bool = primaryKey
        self.__name: str|None = name
    
    @final
    def IsPrimaryKey(self) -> bool:
        return self.__primaryKey
    @final
    def GetName(self) -> str|None:
        return self.__name

class ColumnConfigDecorator(Abstract):
    def __init__(self, config: IColumnConfig) -> None:
        super().__init__()

        self.__config: IColumnConfig = config
    
    @final
    def __call__[TEntity: Entity, TValue](self, func: Property[TEntity, TValue]) -> IColumn[TEntity, TValue]:
        return _Column[TEntity, TValue](func, self.__config)

def columnConfig(primaryKey: bool = False, name: str|None = None) -> ColumnConfigDecorator:
    return ColumnConfigDecorator(ColumnConfig(primaryKey, name))

class ICookie(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue[TEntity: Entity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue]) -> TValue:
        pass
    @abstractmethod
    def SetValue[TEntity: Entity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue], value: TValue) -> None:
        pass

class _Column[TEntity: Entity, TValue](FunctionDecorator[TEntity, TValue], IColumn[TEntity, TValue]):
    def __init__(self, func: Property[TEntity, TValue], config: IColumnConfig) -> None:
        super().__init__(func)

        self.__parameter: ColumnParameter[TEntity, TValue] = ColumnParameter[TEntity, TValue](func, config)
    
    @final
    def GetColumnParameter(self) -> ColumnParameter[TEntity, TValue]:
        return self.__parameter
    
    @final
    def _SetEntityValue(self, obj: Entity, value: object) -> None:
        obj._GetCookie().SetValue(obj, self.__parameter.GetColumnName(), cast(Property[Entity, object], self._GetFunc()), value) # pyright: ignore[reportPrivateUsage]
    
    @overload
    def __get__(self, obj: TEntity, objtype: type|None = None) -> TValue:
        ...
    @overload
    def __get__(self, obj: None, objtype: type|None = None) -> ColumnParameter[TEntity, TValue]:
        ...
    
    @final
    def __get__(self, obj: TEntity|None, objtype: type|None = None) -> TValue|ColumnParameter[TEntity, TValue]:
        if obj is None:
            return self.GetColumnParameter()
        
        return obj._GetCookie().GetValue(obj, self.__parameter.GetColumnName(), self._GetFunc()) # pyright: ignore[reportPrivateUsage]
    @final
    def __set__(self, obj: TEntity, value: TValue) -> None:
        obj._GetCookie().SetValue(obj, self.__parameter.GetColumnName(), self._GetFunc(), value) # pyright: ignore[reportPrivateUsage]

def tableConfig(name: str) -> Selector[Type[Entity]]:
    def decorator(cls: Type[Entity]) -> Type[Entity]:
        def getColumns() -> Generator[IColumnBase]:
            for member in cls.__dict__.values():
                if isinstance(member, _Column):
                    member.GetColumnParameter()._SetTableName(name) # pyright: ignore[reportPrivateUsage]
                    
                    yield member
        
        cls.__columns = ValueFunction[ITuple[IColumnBase]](CreateTuple(getColumns())) # pyright: ignore[reportPrivateUsage]

        return cls
    return decorator

class _EntityUpdater(ValueFunctionUpdater[ITuple[IColumnBase]]):
    def __init__(self, t: Type[Entity], updater: Method[IFunction[ITuple[IColumnBase]]]) -> None:
        super().__init__(updater)

        self.__type: Type[Entity] = t
    
    @final
    def _GetValue(self) -> ITuple[IColumnBase]:
        return CreateTuple(WhereOfType(IColumnBase, self.__type.__dict__.values())) # type: ignore[type-abstract]

class Entity(Abstract, IDisposable):
    @final
    class _AppCookie(Abstract, ICookie):
        def __init__(self) -> None:
            super().__init__()
        
        def GetValue[TEntity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue]) -> TValue:
            return func(obj).GetValue()
        def SetValue[TEntity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue], value: TValue) -> None:
            return func(obj).SetValue(value)
    @final
    class _DBCookie(Abstract, ICookie):
        def __init__(self) -> None:
            super().__init__()

            self.__values: IDictionary[IString, Any] = Dictionary[IString, Any]()
        
        def GetValue[TEntity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue]) -> TValue:
            return cast(TValue, self.__values.TryGetValue(String(name)).GetValue())
        def SetValue[TEntity, TValue](self, obj: TEntity, name: str, func: Property[TEntity, TValue], value: TValue) -> None:
            _name: IString = String(name)

            if not self.__values.TrySetAt(_name, value):
                self.__values.Add(_name, value)
    
    __columns: IFunction[ITuple[IColumnBase]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        def update(func: IFunction[ITuple[IColumnBase]]) -> None:
            cls.__columns = func
        
        super().__init_subclass__(**kwargs)
        
        cls.__columns = _EntityUpdater(cls, update) 

    @classmethod
    def _GetColumns(cls) -> ITuple[IColumnBase]:
        return cls.__columns.GetValue()
    
    def __init__(self) -> None:
        super().__init__()

        self.__cookie: ICookie = Entity._AppCookie()
    
    def _InitCookie(self) -> None:
        self.__cookie = Entity._DBCookie()
    
    def _GetCookie(self) -> ICookie:
        return self.__cookie

class EntityCollection[T: Entity](Abstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetType(self) -> Type[T]:
        pass
    
    def Where(self, connection: IConnection, conditions: _IRoot) -> IEnumerable[T]:
        def getDefaultTableName() -> str:
            return self._GetType().__name__

        def asColumn(column: ColumnParameterAbstract) -> ITableColumn:
            return column._AsColumn(getDefaultTableName()) # pyright: ignore[reportPrivateUsage]

        def iterate(items: ISelectionQueryExecutionResult) -> Generator[T]:
            def createEntity(row: Sequence[object]) -> T:
                obj: T = object.__new__(self._GetType())

                obj._InitCookie() # pyright: ignore[reportPrivateUsage]

                for column, value in zip(columns.AsIterable(), row):
                    column._SetEntityValue(obj, value) # pyright: ignore[reportPrivateUsage]

                obj.Initialize()

                return obj
            
            for row in items.AsIterable():
                yield createEntity(row)

        columns: ITuple[IColumnBase] = self._GetType()._GetColumns() # pyright: ignore[reportPrivateUsage]

        items: ISelectionQueryExecutionResult|None = connection.GetQueryFactory().GetSelectionQuery(
            TableParameterSet.CreateFromNames(String(self._GetType().__name__)),
            CreateColumnParameterSet(Select(columns.AsIterable(), lambda column: asColumn(column.GetColumnParameter()))),
            TryCreateConditionSetFromConditions(_Set(conditions, getDefaultTableName()))).Execute()
        # Select(conditions, lambda condition: CreateKeyValuePair(asColumn(condition.GetKey()), condition.GetValue()))
        return GetEmptyEnumerable() if items is None else IteratorProvider[T](lambda: iterate(items))