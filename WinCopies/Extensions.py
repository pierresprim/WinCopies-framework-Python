from WinCopies import AskConfirmation, ReadInt
from WinCopies.Typing.Delegate import Action, Method, Function, Predicate

def AskInt(message: str, predicate: Predicate[int], errorMessage: str = "The value is out of range."):
    value: int = 0
    
    def loop() -> int:
        return ReadInt(message)
    
    value = loop()
    
    while predicate(value):
        print(errorMessage)
        
        value = loop()
    
    return value

def Process(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    while AskConfirmation(message, info, value):
        action()

def DoProcess(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def TryPredicate(predicate: Predicate[Exception], action: Action) -> bool|None:
    ok: bool = True
    _predicate: Predicate[Exception]

    def __predicate(e: Exception) -> bool:
        nonlocal ok
        nonlocal _predicate

        if predicate(e):
            ok = False
            _predicate = predicate

            return True
        
        return False
    
    _predicate = __predicate
    
    while True:
        try:
            action()

        except Exception as e:
            if _predicate(e):
                continue
            
            return None
        
        break

    return ok
def Try(action: Action, onError: Method[Exception], func: Function[bool]) -> bool|None:
    def _onError(e: Exception) -> bool:
        onError(e)
        
        return func()
    
    return TryPredicate(_onError, action)
def TryMessage(action: Action, onError: Method[Exception], message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))