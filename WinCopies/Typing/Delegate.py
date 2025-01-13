from typing import Callable

type Predicate[T] = Callable[[T], bool]
type Converter[TIn, TOut] = Callable[[TIn], TOut]