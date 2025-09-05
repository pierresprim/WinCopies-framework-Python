import sys
import subprocess

from collections.abc import Iterable

from WinCopies.Collections import Iteration
from WinCopies.Typing import Reflection
from WinCopies.Typing.Pairing import DualResult, KeyValuePair

def Run(command: str|Iterable[str], captureOutput: bool = False, shell: bool = False, throwOnError: bool = True) -> DualResult[object, int]:
    args: str|list[str]|None = None
    
    if Reflection.IsOf(command, str, list):
        args = command # type: ignore
    
    elif Reflection.IsOf(command, Iterable):
        args = list(command)

    else:
        raise ValueError(f"command must be a string, Iterable[str] or list[str]. Command is {type(command)}", command)
    
    result: subprocess.CompletedProcess[str] = subprocess.run(args, stdout = (None if captureOutput else sys.__stdout__), shell = shell, capture_output = captureOutput, check = throwOnError, text = captureOutput)
    
    return DualResult(result.stdout, result.returncode)

def RunWithArgs(command: str, args: Iterable[str], captureOutput: bool = False, shell: bool = False, throwOnError: bool = True) -> DualResult[object, int]:
    return Run(Iteration.PrependValues(args, command), captureOutput, shell, throwOnError)
def RunWithArgValues(command: str, captureOutput: bool, shell: bool, throwOnError: bool, *args: str) -> DualResult[object, int]:
    return RunWithArgs(command, args, captureOutput, shell, throwOnError)

def GetArgument(name: str, argument: str|None) -> str:
    return f"--{name}{None if argument is None else ' ' + argument}"
def TryGetArgument(name: str, argument: str|None) -> str|None:
    return None if argument is None else f"--{name} {argument}"

def GetArgumentTuple(name: str, argument: str) -> tuple[str]:
    return (GetArgument(name, argument),)

def GetArgumentPair(name: str, key: object, value: object) -> str:
    return GetArgument(name, f"{key}:{value}")
def GetArgumentKeyValuePair[TKey, TValue](name: str, pair: KeyValuePair[TKey, TValue]) -> str:
    return GetArgumentPair(name, pair.GetKey(), pair.GetValue())