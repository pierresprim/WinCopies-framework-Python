from enum import Enum

from WinCopies.Data.Factory import IFieldFactory
from WinCopies.Data.Field import FieldType, FieldAttributes, IntegerMode, RealMode, TextMode, IField

def GetField(fieldFactory: IFieldFactory, name: str, attribute: FieldAttributes, fieldType: FieldType, fieldMode: Enum|None) -> IField:
    def checkField(modeType: type[Enum]) -> None:
        if not isinstance(fieldMode, modeType):
            raise ValueError(f"fieldMode must be a value of the {modeType.__name__} enumeration.")
    
    def checkSimpleField() -> None:
        if fieldMode is not None:
            raise ValueError(f"fieldType is {fieldType.name} but fieldMode is not None.")
    
    match fieldType:
        case FieldType.Boolean:
            checkSimpleField()

            return fieldFactory.CreateBool(name, attribute)
        
        case FieldType.Integer:
            checkField(IntegerMode)
            
            return fieldFactory.CreateInteger(name, attribute, fieldMode) # type: ignore
        case FieldType.Real:
            checkField(RealMode)

            return fieldFactory.CreateReal(name, attribute, fieldMode) # type: ignore
        case FieldType.Text:
            checkField(TextMode)

            return fieldFactory.CreateText(name, attribute, fieldMode) # type: ignore
        
        case FieldType.Null:
            checkSimpleField()

            return fieldFactory.CreateNull(name, attribute)
    
    raise ValueError(f"Wrong {FieldType.__name__}.")