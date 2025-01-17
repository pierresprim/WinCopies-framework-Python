import sys
import subprocess

from collections.abc import Iterable

from WinCopies import Typing
from WinCopies.Collections import Iteration
from WinCopies.Typing.Pairing import DualResult, KeyValuePair

def Run(command: str|Iterable[str], captureOutput = False, shell = False, throwOnError = True) -> DualResult[object, int]:
    args: str|list[str]|None = None
    
    if Typing.IsOf(command, str, list):
        args = command
    
    elif Typing.IsOf(command, Iterable):
        args = list(command)

    else:
        raise ValueError(f"command must be a string, Iterable[str] or list[str]. Command is {type(command)}", command)
    
    result: subprocess.CompletedProcess = subprocess.run(args, capture_output = captureOutput, shell = shell, text = captureOutput, check = throwOnError, stdout = None if captureOutput else sys.__stdout__)
    
    return DualResult(result.stdout, result.returncode)

def RunWithArgs(command: str, args: Iterable[str], captureOutput = False, shell = False, throwOnError = True) -> DualResult[object, int]:
    return Run(Iteration.PrependValues(args, command), captureOutput, shell, throwOnError)
def RunWithArgValues(command: str, captureOutput, shell, throwOnError, *args: str) -> DualResult[object, int]:
    return RunWithArgs(command, args, captureOutput, shell, throwOnError)

def GetArgument(name: str, argument: str|None) -> str:
    return f"--{name}{None if argument is None else ' ' + argument}"
def TryGetArgument(name: str, argument: str|None) -> str|None:
    return None if argument is None else f"--{name} {argument}"

def GetArgumentTuple(name: str, argument: str) -> tuple:
    return (GetArgument(name, argument),)

def GetArgumentPair(name: str, key: str, value: str) -> str:
    return GetArgument(name, f"{key}:{value}")
def GetArgumentKeyValuePair[TKey, TValue](name: str, pair: KeyValuePair[TKey, TValue]) -> str:
    return GetArgumentPair(name, pair.GetKey(), pair.GetValue())