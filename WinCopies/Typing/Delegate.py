from typing import Callable

type Predicate[T] = Callable[[T], bool]