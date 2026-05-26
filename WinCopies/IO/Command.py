import sys
import subprocess

from collections.abc import Iterable, Sequence

from WinCopies.Collections.Iteration import PrependValues
from WinCopies.Collections.Util import MakeSequence
from WinCopies.Typing.Pairing import DualResult, KeyValuePair, CreateDualResult

def Run(command: str|Iterable[str], captureOutput: bool = False, shell: bool = False, throwOnError: bool = True) -> DualResult[object, int]:
    result: subprocess.CompletedProcess[str] = subprocess.run(command if isinstance(command, str) or isinstance(command, list) else list(command), stdout = (None if captureOutput else sys.__stdout__), shell = shell, capture_output = captureOutput, check = throwOnError, text = captureOutput)
    
    return CreateDualResult(result.stdout, result.returncode)

def RunWithArgs(command: str, args: Iterable[str], captureOutput: bool = False, shell: bool = False, throwOnError: bool = True) -> DualResult[object, int]:
    return Run(PrependValues(args, command), captureOutput, shell, throwOnError)
def RunWithArgValues(command: str, captureOutput: bool, shell: bool, throwOnError: bool, *args: str) -> DualResult[object, int]:
    return RunWithArgs(command, args, captureOutput, shell, throwOnError)

def GetArgument(name: str, argument: str|None) -> str:
    return f"--{name}{None if argument is None else ' ' + argument}"
def TryGetArgument(name: str, argument: str|None) -> str|None:
    return None if argument is None else f"--{name} {argument}"

def GetArgumentSequence(name: str, argument: str) -> Sequence[str]:
    return MakeSequence(GetArgument(name, argument))

def GetArgumentPair(name: str, key: object, value: object) -> str:
    return GetArgument(name, f"{key}:{value}")
def GetArgumentKeyValuePair[TKey, TValue](name: str, pair: KeyValuePair[TKey, TValue]) -> str:
    return GetArgumentPair(name, pair.GetKey(), pair.GetValue())