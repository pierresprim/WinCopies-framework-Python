from typing import Callable

type Action = Callable[[], None]
type Method[T] = Callable[[T], None]
type Function[T] = Callable[[], T]
type Converter[TIn, TOut] = Callable[[TIn], TOut]
type Predicate[T] = Converter[T, bool]
type Selector[T] = Converter[T, T]