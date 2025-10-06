from enum import Enum, Flag
from typing import Callable, Type

def GetAssertionError(errorMessage: str|None = "Invalid operation."):
    """Creates an AssertionError with the specified message.

    Args:
        errorMessage: The error message for the assertion. Defaults to "Invalid operation.".

    Returns:
        An AssertionError instance with the provided message.
    """
    return AssertionError(errorMessage)

def Throw(errorMessage: str|None = "Invalid operation.") -> None:
    """Raises an AssertionError with the specified message.

    Args:
        errorMessage: The error message for the assertion. Defaults to "Invalid operation.".

    Raises:
        AssertionError: Always raised with the provided message.
    """
    raise GetAssertionError(errorMessage)

def __EnsureFalse(condition: bool, errorMessage: str|None) -> None:
    if condition: Throw(errorMessage)
def __EnsureTrue(condition: bool, errorMessage: str|None) -> None:
    __EnsureFalse(not condition, errorMessage)

def __TryEnsure(condition: bool|object, errorMessage: str|None, action: Callable[[bool, str|None], None]) -> bool:
    if isinstance(condition, bool):
        action(condition, errorMessage)

        return True
    
    return False
def __Ensure(condition: bool, errorMessage: str|None, action: Callable[[bool, str|None], None]) -> None:
    if not __TryEnsure(condition, errorMessage, action):
        raise ValueError(condition)

def EnsureFalse(condition: bool, errorMessage: str|None = "Invalid operation.") -> None:
    """Ensures a condition is False.

    Args:
        condition: The condition to verify.
        errorMessage: The error message if the condition is not False. Defaults to "Invalid operation.".

    Raises:
        AssertionError: If the condition is True.
        ValueError: If the condition is not a boolean.
    """
    __Ensure(condition, errorMessage, __EnsureFalse)
def EnsureTrue(condition: bool, errorMessage: str|None = "Invalid operation.") -> None:
    """Ensures a condition is True.

    Args:
        condition: The condition to verify.
        errorMessage: The error message if the condition is not True. Defaults to "Invalid operation.".

    Raises:
        AssertionError: If the condition is False.
        ValueError: If the condition is not a boolean.
    """
    __Ensure(condition, errorMessage, __EnsureTrue)

def __EnsureValue(value: object|None, errorMessage: str|None, action: Callable[[bool, str|None], None]) -> None:
    action(value is None, errorMessage)

def EnsureNone(value: object|None, errorMessage: str|None = "value must be None.") -> None:
    """Ensures a value is None.

    Args:
        value: The value to verify.
        errorMessage: The error message if the value is not None. Defaults to "value must be None.".

    Raises:
        AssertionError: If the value is not None.
    """
    __EnsureValue(value, errorMessage, EnsureTrue)
def EnsureValue(value: object|None, errorMessage: str|None = "value must not be None.") -> None:
    """Ensures a value is not None.

    Args:
        value: The value to verify.
        errorMessage: The error message if the value is None. Defaults to "value must not be None.".

    Raises:
        AssertionError: If the value is None.
    """
    __EnsureValue(value, errorMessage, EnsureFalse)

def TryEnsureFalse(condition: bool, errorMessage: str|None = "Invalid operation.") -> bool:
    """Tries to ensure a condition is False.

    Args:
        condition: The condition to verify.
        errorMessage: The error message if the condition is not False. Defaults to "Invalid operation.".

    Returns:
        True if the condition was validated (is a boolean), False otherwise.

    Raises:
        AssertionError: If the condition is True.
    """
    return __TryEnsure(condition, errorMessage, __EnsureFalse)
def TryEnsureTrue(condition: bool, errorMessage: str|None = "Invalid operation.") -> bool:
    """Tries to ensure a condition is True.

    Args:
        condition: The condition to verify.
        errorMessage: The error message if the condition is not True. Defaults to "Invalid operation.".

    Returns:
        True if the condition was validated (is a boolean), False otherwise.

    Raises:
        AssertionError: If the condition is False.
    """
    return __TryEnsure(condition, errorMessage, __EnsureTrue)

def EnsureSubclass[T](c: type, t: Type[T], errorMessage: str|None = "c must be a subclass of t.") -> None:
    """Ensures a class is a subclass of another class.

    Args:
        c: The class to verify.
        t: The expected parent class.
        errorMessage: The error message if c is not a subclass of t. Defaults to "c must be a subclass of t.".

    Raises:
        AssertionError: If c is not a subclass of t.
    """
    EnsureTrue(issubclass(c, t), errorMessage)
def EnsureEnum(e: type) -> None:
    """Ensures a type is an enum.

    Args:
        e: The type to verify.

    Raises:
        AssertionError: If e is not an enum type.
    """
    EnsureSubclass(e, Enum, "e must be an enum.")
def EnsureFlagEnum(e: type) -> None:
    """Ensures a type is a Flag enum.

    Args:
        e: The type to verify.

    Raises:
        AssertionError: If e is not a Flag enum type.
    """
    EnsureSubclass(e, Flag, "e must be Flag enum.")