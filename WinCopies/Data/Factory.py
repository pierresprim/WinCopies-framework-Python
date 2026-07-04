from abc import abstractmethod
from collections.abc import Iterable
from typing import Callable, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Abstraction.Collection import CreateTuple
from WinCopies.Collections.Abstraction.Mapping import CreateSet
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Expression import ICompositeExpressionNode, CompositeExpressionNode, CompositeExpressionValueNode
from WinCopies.Collections.Extensions import ITuple, IHashableTuple, IDictionary, IReadOnlyKeyedSet
from WinCopies.Collections.Iteration import TryGenerate, GetFirst, Select, ExpandItems
from WinCopies.Collections.Iteration.Batch import Batch, IHandler
from WinCopies.Collections.Util import MakeGenerator

from WinCopies.Typing.Delegate import Converter
from WinCopies.Typing.Object import IValueItem, IString, Map
from WinCopies.Typing.Pairing import IKeyValuePair, DualResult, CreateDualResult



from WinCopies.Data import Operator, ConditionalOperator, IColumn, IOperandValue, SetOperand, QueryErrorKinds, QueryError
from WinCopies.Data.Field import FieldAttributes, GenericField, BooleanField, IntegerField, RealField, TextField, IntegerMode, RealMode, TextMode
from WinCopies.Data.Index import ISingleColumnIndex, IMultiColumnIndex, IMultiColumnKey, IForeignKey
from WinCopies.Data.Parameter import IFormattable, IParameter, CreateFieldParameter, CreateFieldParameterFromValue
from WinCopies.Data.Query import ISelectionQuery, IInsertionQuery, IMultiInsertionQuery, IWriteQuery, IUpdateQuery
from WinCopies.Data.Set import IColumnParameterSet, ITableParameterSet
from WinCopies.Data.Set.Extensions import IConditionParameterSet, FieldConditionNodeSet, AsColumns, MakeConjunctionSet, CreateConditionSet

class IFieldFactory(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateNull(self, name: str, attribute: FieldAttributes) -> GenericField:
        ...

    @abstractmethod
    def CreateBool(self, name: str, attribute: FieldAttributes) -> BooleanField:
        ...
    
    @abstractmethod
    def CreateInteger(self, name: str, attribute: FieldAttributes, mode: IntegerMode) -> IntegerField:
        ...
    @abstractmethod
    def CreateReal(self, name: str, attribute: FieldAttributes, mode: RealMode) -> RealField:
        ...
    @abstractmethod
    def CreateText(self, name: str, attribute: FieldAttributes, mode: TextMode) -> TextField:
        ...

class IQueryFactoryBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryBuildConditionsByKeys(self, keys: IReadOnlyKeyedSet[IString, object], maxParameterCount: int|None = None, handler: IHandler|None = None) -> Generator[IConditionParameterSet]|None:
        ...
    @final
    def BuildConditionsByKeys(self, keys: IReadOnlyKeyedSet[IString, object], maxParameterCount: int|None = None, handler: IHandler|None = None) -> Generator[IConditionParameterSet]:
        return TryGenerate(self.TryBuildConditionsByKeys(keys, maxParameterCount, handler))
class IQueryFactory(IQueryFactoryBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetSelectionQuery(self, tables: ITableParameterSet|str, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        ...

    @abstractmethod
    def GetInsertionQuery(self, tableName: str, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        ...
    @abstractmethod
    def GetMultiInsertionQuery(self, tableName: str, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        ...
    
    @abstractmethod
    def GetUpdateQuery(self, tableName: str, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IUpdateQuery:
        ...
    
    @abstractmethod
    def GetDeletionQuery(self, tableName: str, conditions: IConditionParameterSet) -> IWriteQuery:
        ...

class ITableQueryFactory(IQueryFactoryBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetSelectionQuery(self, columns: IColumnParameterSet[IFormattable], conditions: IConditionParameterSet|None = None) -> ISelectionQuery:
        ...

    @abstractmethod
    def GetInsertionQuery(self, items: IDictionary[IString, object], ignoreExisting: bool = False) -> IInsertionQuery:
        ...
    @abstractmethod
    def GetMultiInsertionQuery(self, columns: ICountableEnumerable[IString], items: Iterable[Iterable[object]], ignoreExisting: bool = False) -> IMultiInsertionQuery:
        ...
    
    @abstractmethod
    def GetUpdateQuery(self, values: IDictionary[IString, object], conditions: IConditionParameterSet) -> IUpdateQuery:
        ...
    
    @abstractmethod
    def GetDeletionQuery(self, conditions: IConditionParameterSet) -> IWriteQuery:
        ...

class QueryFactory(Abstract, IQueryFactory):
    def __init__(self) -> None: super().__init__()

    @final
    def TryBuildConditionsByKeys(self, keys: IReadOnlyKeyedSet[IString, object], maxParameterCount: int|None = None, handler: IHandler|None = None) -> Generator[IConditionParameterSet]|None:
        def process() -> Generator[IConditionParameterSet]:
            def getColumns() -> ITuple[IColumn]: return CreateTuple(AsColumns(Select(keys.GetKeys().AsIterable(), lambda column: column.GetValue())))
            
            def onSinglePrimaryKey(columns: ITuple[IColumn], values: Iterable[ITuple[object]]) -> Generator[IConditionParameterSet]:
                def process(column: IColumn, values: Iterable[IValueItem]) -> IConditionParameterSet|None: return MakeConjunctionSet(CreateDualResult(column, CreateFieldParameter(SetOperand[IValueItem](CreateSet(values)))))
                
                conditionSet: IConditionParameterSet|None = process(GetFirst(columns.AsIterable()).GetValue(), Select(values, lambda items: Map(items.GetAt(0))))

                return MakeGenerator() if conditionSet is None else MakeGenerator(conditionSet)
            def onCompositePrimaryKey(columns: ITuple[IColumn], values: Iterable[ITuple[object]]) -> Generator[IConditionParameterSet]:
                def process(columns: Iterable[IColumn], iterator: Generator[Iterable[IValueItem]]) -> IConditionParameterSet:
                    def processItems(columns: Iterable[IColumn], values: Iterable[IValueItem]) -> Generator[IKeyValuePair[IColumn, IParameter[IOperandValue]|None]]:
                        for items in zip(columns, values): yield CreateDualResult(items[0], CreateFieldParameterFromValue(Operator.Equals, items[1]))
                    
                    def process(columns: Iterable[IColumn], values: Iterable[IValueItem]) -> ICompositeExpressionNode[IKeyValuePair[IColumn, IParameter[IOperandValue]|None], ConditionalOperator]:
                        iterator: Generator[IKeyValuePair[IColumn, IParameter[IOperandValue]|None]] = processItems(columns, values)
                        first: IKeyValuePair[IColumn, IParameter[IOperandValue]|None] = GetFirst(iterator).GetValue()
                        node: ICompositeExpressionNode[IKeyValuePair[IColumn, IParameter[IOperandValue]|None], ConditionalOperator] = CompositeExpressionNode[IKeyValuePair[IColumn, IParameter[IOperandValue]|None], ConditionalOperator](CompositeExpressionValueNode[IKeyValuePair[IColumn, IParameter[IOperandValue]|None], ConditionalOperator](first))

                        for items in iterator: node.GetLast().SetNext(ConditionalOperator.And, items)

                        return node

                    root: FieldConditionNodeSet[IColumn] = FieldConditionNodeSet[IColumn](process(columns, GetFirst(iterator).GetValue()))
                    
                    for items in iterator: root.GetLast().SetNextExpression(ConditionalOperator.Or, process(columns, items))

                    return CreateConditionSet(root)
                
                yield process(columns.AsIterable(), Select(values, lambda items: Select(items.AsIterable(), lambda value: Map(value))))
            
            def getProcessor() -> Converter[Iterable[ITuple[object]], Generator[IConditionParameterSet]]:
                processor: Callable[[ITuple[IColumn], Iterable[ITuple[object]]], Generator[IConditionParameterSet]] = onSinglePrimaryKey if pkCount == 1 else onCompositePrimaryKey
                columns: ITuple[IColumn] = getColumns()

                return lambda keys: processor(columns, keys)

            pkCount: int = keys.GetKeys().GetCount()

            if maxParameterCount is None: return getProcessor()(keys.AsIterable())
            if maxParameterCount < pkCount: raise QueryError(QueryErrorKinds.ParameterLimitExceeded)
            
            return ExpandItems(Batch(maxParameterCount // pkCount, keys, handler), getProcessor())

        return process() if keys.HasItems() else None

class IIndexFactory(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetPrimaryKey(self, name: str, columns: IHashableTuple[IString]|Iterable[IString]) -> IMultiColumnKey:
        ...
    @abstractmethod
    def GetForeignKey(self, name: str, column: str, foreignKey: DualResult[str, str]) -> IForeignKey:
        ...
    @abstractmethod
    def GetNormalIndex(self, name: str, column: str) -> ISingleColumnIndex:
        ...
    @abstractmethod
    def GetUnicityIndex(self, name: str, columns: IHashableTuple[IString]|Iterable[IString]) -> IMultiColumnIndex:
        ...