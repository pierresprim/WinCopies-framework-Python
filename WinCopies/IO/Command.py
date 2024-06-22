import sys
import subprocess

from collections.abc import Iterable

from WinCopies import DualResult, KeyValuePair, String

def Run(command: str, captureOutput = False, throwOnError = True) -> DualResult[object, int]:
    result: subprocess.CompletedProcess = subprocess.run(command, capture_output=captureOutput, shell=True, text=captureOutput)
    
    if throwOnError:
        result.check_returncode()
    
    return DualResult(result.stdout, result.returncode)