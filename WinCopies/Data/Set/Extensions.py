from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable
from typing import final



from WinCopies import IInterface, Abstract

from WinCopies.Collections import Generator, MakeSequence
from WinCopies.Collections.Abstraction.Collection import Dictionary
from WinCopies.Collections.Enumeration.Recursive import IRecursiveEnumerationHandler
from WinCopies.Collections.Expression import ICompositeExpression, ICompositeExpressionNode, IConnector, CompositeExpressionRoot, CompositeExpressionValueRoot, MakeCompositeExpressionRoot
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Loop import DoForEachItem

from WinCopies.Delegates import Self

from WinCopies.String import StringifyIfNone

from WinCopies.Typing import InvalidOperationError, INullable
from WinCopies.Typing.Delegate import Method, Selector
from WinCopies.Typing.Object import IValueProvider, IValueItem, IBoolean, IString, GetFalseObject
from WinCopies.Typing.Pairing import IKeyValuePair



from WinCopies.Data import ConditionalOperator, IColumn, Column, TableColumn, IOperand, IOperandValue
from WinCopies.Data.Misc import JoinType
from WinCopies.Data.Parameter import IParameter, ITableParameter
from WinCopies.Data.QueryBuilder import IJoinBase, IConditionalQueryWriter, ISelectionQueryWriter, IParameterSetBase
from WinCopies.Data.Set import IParameterSet, IColumnParameterSet, IFieldParameterSet, ITableParameterSet

class IConditionParameterSet(IParameterSetBase[IConditionalQueryWriter]):
    def __init__(self):
        super().__init__()

class IBranchSet[T: IValueProvider](IParameterSetBase[ISelectionQueryWriter]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetAlias(self) -> str:
        pass

    @abstractmethod
    def GetDefault(self) -> T:
        pass

class ICaseSet[TKey: IValueItem, TValue](IBranchSet[TKey]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetColumn(self) -> IColumn:
        pass
    
    @abstractmethod
    def GetConditions(self) -> IDictionary[TKey, TValue]:
        pass

class IExistenceQuery(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetTableName(self) -> str:
        pass
    
    @abstractmethod
    def GetTableParameter(self) -> ITableParameter[object]|None:
        pass

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        pass
    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        pass

    @abstractmethod
    def GetConditions(self) -> IConditionParameterSet|None:
        pass
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass
class ExistenceQuery(IExistenceQuery):
    def __init__(self, tableName: str, tableParameter: ITableParameter[object]|None, conditions: IConditionParameterSet|None = None):
        super().__init__()

        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object]|None = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
        self.__joins: Iterable[IJoin]|None = None
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]|None:
        return self.__tableParameter

    @abstractmethod
    def GetJoins(self) -> Iterable[IJoin]|None:
        return self.__joins
    @abstractmethod
    def SetJoins(self, joins: Iterable[IJoin]|None) -> None:
        self.__joins = joins
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        self.__conditions = conditions

class IExistenceSet(IBranchSet[IBoolean]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetQuery(self) -> IExistenceQuery:
        pass

class IMatchSet[T: IValueItem](ICaseSet[T, T]):
    def __init__(self):
        super().__init__()
class IConditionSet[TKey: IValueItem, TValue](ICaseSet[TKey, IParameter[IOperand[TValue]]]):
    def __init__(self):
        super().__init__()
class IIfSet[T: IValueItem](ICaseSet[T, IConditionParameterSet]):
    def __init__(self):
        super().__init__()

class ParameterSet[T](Dictionary[IColumn, T], IParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T]|None = None):
        super().__init__(dictionary)

class ColumnParameterSet[T: IParameter[object]](ParameterSet[T|None], IColumnParameterSet[T]):
    def __init__(self, dictionary: dict[IColumn, T|None]|None = None):
        super().__init__(dictionary)
    
    @staticmethod
    def Create(columns: Iterable[IColumn]) -> IColumnParameterSet[T]:
        return ColumnParameterSet(dict.fromkeys(columns))
    
    @staticmethod
    def CreateFromNames(columnNames: Iterable[str], tableName: str|None = None) -> IColumnParameterSet[T]:
        return ColumnParameterSet[T].Create(Select(columnNames, (lambda columnName: Column(columnName)) if tableName is None else (lambda columnName: TableColumn(tableName, columnName))))

class FieldParameterNodeSet[T: IParameter[IOperandValue]](CompositeExpressionRoot[IKeyValuePair[IColumn, T], ConditionalOperator], IFieldParameterSet[T]):
    def __init__(self, initialNode: ICompositeExpressionNode[IKeyValuePair[IColumn, T], ConditionalOperator]):
        super().__init__(initialNode)
class FieldParameterSet[T: IParameter[IOperandValue]](CompositeExpressionValueRoot[IKeyValuePair[IColumn, T], ConditionalOperator], IFieldParameterSet[T]):
    def __init__(self, initialValue: IKeyValuePair[IColumn, T]):
        super().__init__(initialValue)

def __MakeFieldParameterSet[T: IParameter[IOperandValue]](conditionalOperator: ConditionalOperator, *conditions: IKeyValuePair[IColumn, T]) -> IFieldParameterSet[T]|None:
    return MakeCompositeExpressionRoot(lambda condition: FieldParameterSet[T](condition), Self, conditionalOperator, *conditions)

def MakeFieldParameterConjonctionSet[T: IParameter[IOperandValue]](*conditions: IKeyValuePair[IColumn, T]) -> IFieldParameterSet[T]|None:
    return __MakeFieldParameterSet(ConditionalOperator.And, *conditions)
def MakeFieldParameterDisjonctionSet[T: IParameter[IOperandValue]](*conditions: IKeyValuePair[IColumn, T]) -> IFieldParameterSet[T]|None:
    return __MakeFieldParameterSet(ConditionalOperator.Or, *conditions)

class TableParameterSet(Dictionary[IString, ITableParameter[object]|None], ITableParameterSet):
    def __init__(self, dictionary: dict[IString, ITableParameter[object]|None]|None = None):
        super().__init__(dictionary)
    
    @staticmethod
    def Create(tableNames: Iterable[IString]) -> ITableParameterSet:
        return TableParameterSet(dict[IString, None].fromkeys(tableNames))

class ConditionParameterSet(IConditionParameterSet):
    @final
    class __Handler(IRecursiveEnumerationHandler[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]]):
        def __init__(self, writer: IConditionalQueryWriter, action: Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]], connectorHandlerUpdater: Method[Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]]]):
            super().__init__()

            self.__writer: IConditionalQueryWriter = writer
            self.__action: Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]] = action
            self.__connectorHandlerUpdater: Method[Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]]] = connectorHandlerUpdater
        
        def OnEnteringEnumerationLevel(self, item: ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]) -> None:
            def _action(item: ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]) -> None:
                connector: IConnector[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]|None = item.GetPrevious()

                if connector is not None:
                    self.__writer.Write(str(connector.GetConnector()))
                
                self.__action(item)
            def action(item: ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]) -> None:
                self.__action(item)

                self.__connectorHandlerUpdater(_action)

            self.__writer.Write('(')

            self.__connectorHandlerUpdater(action)
        def OnExitingEnumerationLevel(self, cookie: None) -> None:
            self.__writer.Write(')')
    
    def __init__(self, set: IFieldParameterSet[IParameter[IOperandValue]]):
        super().__init__()

        self.__set: IFieldParameterSet[IParameter[IOperandValue]] = set
    
    @final
    def Render(self, writer: IConditionalQueryWriter) -> None:
        def updateAction(_action: Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]]) -> None:
            nonlocal action

            action = _action
        def process(condition: ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]) -> None:
            nonlocal value

            if (value := condition.TryGetValue()).HasValue():
                writer.Write(writer.ProcessCondition(value.GetValue()))

        value: INullable[IKeyValuePair[IColumn, IParameter[IOperandValue]]]|None = None
        action: Method[ICompositeExpression[IKeyValuePair[IColumn, IParameter[IOperandValue]], ConditionalOperator]] = lambda value: None

        for condition in self.__set.GetRecursiveEnumerable(handler = ConditionParameterSet.__Handler(writer, process, updateAction)).AsIterable():
            action(condition)

def MakeConjonctionSet(*conditions: IKeyValuePair[IColumn, IParameter[IOperandValue]]) -> IConditionParameterSet|None:
    set: IFieldParameterSet[IParameter[IOperandValue]]|None = MakeFieldParameterConjonctionSet(*conditions)

    return None if set is None else ConditionParameterSet(set)
def MakeDisjonctionSet(*conditions: IKeyValuePair[IColumn, IParameter[IOperandValue]]) -> IConditionParameterSet|None:
    set: IFieldParameterSet[IParameter[IOperandValue]]|None = MakeFieldParameterDisjonctionSet(*conditions)

    return None if set is None else ConditionParameterSet(set)

class BranchSetBase[T: IValueProvider](Abstract, IBranchSet[T]):
    def __init__(self, alias: str):
        super().__init__()

        self.__alias: str = alias
    
    @final
    def GetAlias(self) -> str:
        return self.__alias
    
    @abstractmethod
    def _GetColumn(self) -> str|None:
        pass

    @abstractmethod
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        pass
    
    @final
    def Render(self, writer: ISelectionQueryWriter) -> None:
        def getColumnName() -> str:
            columnName: str = StringifyIfNone(self._GetColumn())

            return '' if columnName == '' else ' ' + columnName
        
        writer.Write(f"CASE{getColumnName()}")
        
        self._WriteConditions(writer)
        
        writer.Write(f" ELSE {writer.JoinParameters(MakeSequence(self.GetDefault().GetUnderlyingValue()))} END AS {writer.FormatTableName(self.GetAlias())}")
class BranchSet[T: IValueProvider](BranchSetBase[T]):
    def __init__(self, alias: str, defaultValue: T):
        super().__init__(alias)

        self.__defaultValue: T = defaultValue
    
    @final
    def GetDefault(self) -> T:
        return self.__defaultValue

class ExistenceSet(BranchSetBase[IBoolean], IExistenceSet):
    def __init__(self, alias: str, query: IExistenceQuery):
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
    def GetDefault(self) -> IBoolean:
        return GetFalseObject()
    
    @final
    def GetQuery(self) -> IExistenceQuery:
        return self.__query

class CaseSet[TKey: IValueItem, TValue](BranchSet[TKey], ICaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, conditions: IDictionary[TKey, TValue]|None = None):
        super().__init__(alias, defaultValue)

        self.__column: IColumn = column
        self.__conditions: IDictionary[TKey, TValue] = Dictionary[TKey, TValue]() if conditions is None else conditions
    
    @abstractmethod
    def _RenderValue(self, value: TValue, writer: ISelectionQueryWriter) -> None:
        pass

    @final
    def _WriteConditions(self, writer: ISelectionQueryWriter) -> None:
        def render(item: IKeyValuePair[TKey, TValue]) -> None:
            writer.Write(" WHEN ")

            self._RenderValue(item.GetValue(), writer)

            writer.Write(f" THEN {writer.JoinParameters(MakeSequence(item.GetKey().GetUnderlyingValue()))}")

        if not DoForEachItem(self.GetConditions().AsIterable(), render):
            raise ValueError("No condition given.")
    
    @final
    def GetColumn(self) -> IColumn:
        return self.__column
    
    @final
    def GetConditions(self) -> IDictionary[TKey, TValue]:
        return self.__conditions

class MatchSet[T: IValueItem](CaseSet[T, T], IMatchSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, T]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> str:
        return f"{self.GetColumn()}"
    
    @final
    def _RenderValue(self, value: T, writer: ISelectionQueryWriter) -> None:
        writer.Write(writer.JoinParameters(MakeSequence(value)))

class ConditionalSet[TKey: IValueItem, TValue](CaseSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, dictionary: IDictionary[TKey, TValue]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _GetColumn(self) -> None:
        return None

class ConditionSet[TKey: IValueItem, TValue](ConditionalSet[TKey, IParameter[IOperand[TValue]]], IConditionSet[TKey, TValue]):
    def __init__(self, alias: str, defaultValue: TKey, column: IColumn, dictionary: IDictionary[TKey, IParameter[IOperand[TValue]]]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IParameter[IOperand[TValue]], writer: ISelectionQueryWriter) -> None:
        def getArgument(arguments: Iterable[IOperand[TValue]]) -> Generator[IOperand[TValue]]:
            func: Selector[IOperand[TValue]]|None = None

            def getArgument(argument: IOperand[TValue]) -> IOperand[TValue]:
                nonlocal func

                def throw(_: IOperand[TValue]) -> IOperand[TValue]:
                    raise InvalidOperationError("Only one argument must be given in Case statements.")

                func = throw

                return argument
            
            func = getArgument

            for argument in arguments:
                yield func(argument)
        
        writer.Write(value.Format(self.GetColumn().ToString(writer.FormatTableName), writer.JoinOperands(getArgument(value.AsIterable()))))
class IfSet[T: IValueItem](ConditionalSet[T, IConditionParameterSet], IIfSet[T]):
    def __init__(self, alias: str, defaultValue: T, column: IColumn, dictionary: IDictionary[T, IConditionParameterSet]|None = None):
        super().__init__(alias, defaultValue, column, dictionary)
    
    @final
    def _RenderValue(self, value: IConditionParameterSet, writer: ISelectionQueryWriter) -> None:
        value.Render(writer)

class IJoin(IJoinBase[IConditionParameterSet]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        pass
class Join(IJoin):
    def __init__(self, type: JoinType, tableName: str, tableParameter: ITableParameter[object], conditions: IConditionParameterSet|None = None):
        super().__init__()

        self.__type: JoinType = type
        self.__tableName: str = tableName
        self.__tableParameter: ITableParameter[object] = tableParameter
        self.__conditions: IConditionParameterSet|None = conditions
    
    @final
    def GetType(self) -> JoinType:
        return self.__type
    
    @final
    def GetTableName(self) -> str:
        return self.__tableName
    
    @final
    def GetTableParameter(self) -> ITableParameter[object]:
        return self.__tableParameter
    
    @final
    def GetConditions(self) -> IConditionParameterSet|None:
        return self.__conditions
    @final
    def SetConditions(self, conditions: IConditionParameterSet|None) -> None:
        self.__conditions = conditions