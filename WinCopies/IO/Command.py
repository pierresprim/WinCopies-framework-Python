import sys
import subprocess

from collections.abc import Iterable

from WinCopies import DualResult, KeyValuePair, String

def Run(command: str|Iterable[str], captureOutput = False, shell=False, throwOnError = True) -> DualResult[object, int]:
    result: subprocess.CompletedProcess = subprocess.run(command, capture_output=captureOutput, shell=shell, text=captureOutput, stdout=None if captureOutput else sys.__stdout__)
    
    if throwOnError:
        result.check_returncode()
    
    return DualResult(result.stdout, result.returncode)