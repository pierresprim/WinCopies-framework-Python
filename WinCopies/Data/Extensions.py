from enum import Enum

from WinCopies.Data.Factory import IFieldFactory
from WinCopies.Data.Field import FieldType, FieldAttributes, IntegerMode, RealMode, TextMode, IField

def GetField(fieldFactory: IFieldFactory, name: str, attribute: FieldAttributes, fieldType: FieldType, fieldMode: Enum|None) -> IField:
    def checkField[T: Enum](modeType: type[T]) -> T:
        if isinstance(fieldMode, modeType): return fieldMode
        
        raise ValueError(f"fieldMode must be a value of the {modeType.__name__} enumeration.")
    
    def checkSimpleField() -> None:
        if fieldMode is not None: raise ValueError(f"fieldType is {fieldType.name} but fieldMode is not None.")
    
    match fieldType:
        case FieldType.Boolean:
            checkSimpleField()

            return fieldFactory.CreateBool(name, attribute)
        
        case FieldType.Integer: return fieldFactory.CreateInteger(name, attribute, checkField(IntegerMode))
        case FieldType.Real: return fieldFactory.CreateReal(name, attribute, checkField(RealMode))
        case FieldType.Text: return fieldFactory.CreateText(name, attribute, checkField(TextMode))
        
        case FieldType.Null:
            checkSimpleField()

            return fieldFactory.CreateNull(name, attribute)
    
    raise ValueError(f"Wrong {FieldType}.")