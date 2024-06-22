import sys
import subprocess

from collections.abc import Iterable

from WinCopies import DualResult, KeyValuePair, String

def Run(command: str|Iterable[str], captureOutput = False, shell=False, throwOnError = True) -> DualResult[object, int]:
    result: subprocess.CompletedProcess = subprocess.run(command, capture_output=captureOutput, shell=shell, text=captureOutput, stdout=None if captureOutput else sys.__stdout__)
    
    if throwOnError:
        result.check_returncode()
    
    return DualResult(result.stdout, result.returncode)

def RunWithArgs(command: str, args: Iterable[str], captureOutput = False, throwOnError = True) -> DualResult[object, int]:
    return Run(String.SurroundWith(command, ' ', String.SpaceJoin(args)), captureOutput, throwOnError)
def RunWithArgValues(command: str, captureOutput, throwOnError, *args: str) -> DualResult[object, int]:
    return RunWithArgs(command, args, captureOutput, throwOnError)

def GetArgument(name: str, argument: str|None) -> str:
    return f"--{name}{None if argument is None else ' ' + argument}"
def TryGetArgument(name: str, argument: str|None) -> str|None:
    return None if argument is None else f"--{name} {argument}"

def GetArgumentTuple(name: str, argument: str) -> tuple:
    return (GetArgument(name, argument),)

def GetArgumentPair(name: str, key: str, value: str) -> str:
    return GetArgument(name, f"{key}:{value}")
def GetArgumentKeyValuePair(name: str, pair: KeyValuePair) -> str:
    return GetArgumentPair(name, pair.GetKey(), pair.GetValue())