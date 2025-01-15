from typing import Callable

type Function[T] = Callable[[], T]
type Predicate[T] = Callable[[T], bool]
type Converter[TIn, TOut] = Callable[[TIn], TOut]