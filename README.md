[![Build Status](https://travis-ci.org/dbrattli/aioreactive.svg?branch=master)](https://travis-ci.org/dbrattli/aioreactive)
[![Coverage Status](https://coveralls.io/repos/github/dbrattli/aioreactive/badge.svg?branch=master)](https://coveralls.io/github/dbrattli/aioreactive?branch=master)

# aioreactive - reactive tools for asyncio

Aioreactive is an asynchronous and reactive Python library for asyncio using async and await. Aioreactive is based on concepts from [RxPY](https://github.com/ReactiveX/RxPY), but is more low-level, and integrates more naturally with the Python language.

>aioreactive is the unification of reactive programming and asyncio using async and await.

## The design goals for aioreactive:

* Python 3.5+ only. We have a hard dependency on `async` and `await`.
* All operators and tools are implemented as plain old functions. No methods other than Python special methods.
* Everything is `async`. Sending values is async, listening to sources is async, even mappers or predicates may sleep or perform other async operations.
* One scheduler to rule them all. Everything runs on the asyncio base event-loop.
* No multi-threading. Only async and await with concurrency using asyncio. Threads are hard, and in many cases it doesn’t make sense to use multi-threading in Python applications. If you need to use threads you may wrap them with [`concurrent.futures`](https://docs.python.org/3/library/concurrent.futures.html#module-concurrent.futures) or similar.
* Simple, clean and use few abstractions. Try to align with the itertools package, and reuse as much from the Python standard library as possible.

# Core level

At the core, aioreactive is small low level asynchronous library for reactive programming. This core library may be used directly at the `AsyncSource` level, or one may choose to use higher level abstractions such as `Producer` or `Observable` described further down on this page.

## AsyncSource and AsyncSink

Aioreactive is built around the asynchronous duals of the AsyncIterable and AsyncIterator abstract base classes. These async classes are called AsyncSource and AsyncSink.

AsyncSource is the dual or opposite of AsyncIterable and provides a single setter method called `__alisten__()` that is the dual of the `__aiter__()` getter method:

```python
from abc import ABCMeta, abstractmethod

class AsyncSource(metaclass=ABCMeta):
    @abstractmethod
    async def __alisten__(self, sink):
        return NotImplemented
```

AsyncSink is modelled after the so called [consumer interface](http://effbot.org/zone/consumer.htm), the enhanced generator interface in [PEP-342](https://www.python.org/dev/peps/pep-0342/) and async generators in [PEP-525](https://www.python.org/dev/peps/pep-0525/). It is the dual of the AsyncIterator `__anext__()` method, and provides three async methods `asend()`, that is the opposite of `__anext__()`, `athrow()` that is the opposite of an `raise Exception()` and `aclose()` that is the opposite of `raise StopAsyncIteration`:

```python
from abc import ABCMeta, abstractmethod

class AsyncSink(AsyncSource):
    @abstractmethod
    async def asend(self, value):
        return NotImplemented

    @abstractmethod
    async def athrow(self, error):
        return NotImplemented

    @abstractmethod
    async def aclose(self):
        return NotImplemented

    async def __alisten__(self, sink):
        return self
```

Sinks are also sources. This is similar to how Iterators are also Iterables in Python. This enables sinks to be chained together. While chaining sinks is not normally done when using aioreactive, it's used extensively by the various sources and operators when you listen to them.

## Listening to sources

A sink need to listen to sources in order to receive values sent by the source. The `listen()` function is used to attach a sink to a source. It returns a future when the subscription has been sucessfully set up. `Listener` is an anonymous sink that constructs an `AsyncSink` from plain functions, so you don't have to implement a new sink every time you need.

```python
async def asend(value):
    print(value)

fut = await listen(ys, Listener(asend))
```

To unsubscribe you simply just `cancel()` the future:

```python
fut.cancel()
```

A subscription may also be awaited. It will resolve when the subscription closes either normally or with an error. The value returned will be the last value received through the subscription. If no value has been received when the subscription closes, then await will throw `CancelledError`.

```
value = await (await listen(ys, Listener(asend)))
```

The double await can be replaced by the better looking function `run()` which basically does the same thing:

```
value = await run(ys, Listener(asend))
```

## Streams

A stream if both a sink and a source. Since every sink is also a source, it's better described as as sink that supports multiple listeners. Thus you may both send values, and listen to it at the same time.

```python
xs = Stream()

sink = Listener()
await listen(xs, sink)
await xs.asend(42)
```

You can listen to streams the same was as with any other source.

## Functions and operators

aioreactive contains many of the same operators as you know from Rx. Our goal is not to implement them all, but to have the most essential onces. Other may be added by extension libraries.

* **concat** -- Concatenates two source streams.
* **debounce** -- Throttles a source stream.
* **delay** -- delays the items within a source stream.
* **distinct_until_changed** -- stream with continously distict values.
* **filter** -- filters a source stream.
* **flat_map** -- transforms a stream into a stream of streams and flattens the resulting stream.
* **from_iterable** -- Create a source stream from an (async) iterable.
* **listen** -- Subscribes a sink to a source. Returns a future.
* **map** -- transforms a source stream.
* **merge** -- Merges a stream of streams.
* **run** -- Awaits the future returned by listen. Returns when the subscription closes.
* **slice** -- Slices a source stream.
* **switch_latest** -- Merges the latest stream in a stream of streams.
* **unit** -- Converts a value or future to a source stream.
* **with_latest_from** -- Combines two streams.

# Functional or object-oriented, reactive or interactive

With aioreactive you can choose to program functionally with plain old functions, or object-oriented with classes and methods. There are currently two different implementations layered on top of `AsyncSource` called `Producer`and `Observable`. `Producer` is a functional reactive and interactive world, while `Observable` is an object-oriented and reactive world.

# Producer

## Producers are composed with pipelining

The `Producer` is a functional world built on top of `AsyncSource` and `AsyncIterable`. `Producer` can compose operators using forward pipelining using the `|` (or) operator. The operators are partially applied with arguments.

```python
ys = xs | op.filter(predicate) | op.map(mapper) | op.flat_map(request)
```

## Subscriptions are async iterables

Subscriptions implements `AsyncIterable` so may iterate them asynchronously. They effectively transform us from an async push model to an async pull model. This enable us to use language features such as async-for. We do this without any queueing as push by the `AsyncSource` will await the pull by the `AsyncIterator`.  This effectively applies so-called "back-pressure" up the stream as the source will await the iterator to pick up the next item.

The for-loop may be wrapped with async-with may to control the lifetime of the subscription:

```
xs = Producer.from_iterable([1, 2, 3])
result = []

async with listen(xs) as ys:
    async for x in ys:
        result.append(x)

assert result == [1, 2, 3]
```

Longer pipelines may break lines as for binary operators:

```python
from aioreactive.producer import Stream, op

async def main():
    stream = Stream()

    xs = (stream
          | op.map(lambda x: x["term"])
          | op.filter(lambda text: len(text) > 2)
          | op.debounce(0.75)
          | op.distinct_until_changed()
          | op.map(search_wikipedia)
          | op.switch_latest()
          )

    async with listen(xs) as ys
        async for value in ys:
            print(value)
```

Producers also supports slicing using the Python slice notation.

```python
@pytest.mark.asyncio
async def test_slice_special():
    xs = Producer.from_iterable([1, 2, 3, 4, 5])
    values = []

    async def asend(value):
        values.append(value)

    ys = xs[1:-1]

    result = await run(ys, Listener(asend))

    assert result == 4
    assert values == [2, 3, 4]
```

# Observable

## Async observables and async observers

An alternative to `Producer` and pipelining is to use async observables and method chaining as we know from [ReactiveX](http://reactivex.io). Async Observables are almost the same as the Observables we are used to from [RxPY](https://github.com/ReactiveX/RxPY). The difference is that all methods such as `.subscribe()` and observer methods such as `on_next(value)`, `on_error(err)` and `on_completed()` are all async and needs to be awaited.

```python
@pytest.mark.asyncio
async def test_observable_simple_pipe():
    xs = Observable.from_iterable([1, 2, 3])
    result = []

    async def mapper(value):
        await asyncio.sleep(0.1)
        return value * 10

    async def predicate(value):
        await asyncio.sleep(0.1)
        return value > 1

    ys = xs.where(predicate).select(mapper)

    async def on_next(value):
        result.append(value)

    sub = await ys.subscribe(AnonymousObserver(on_next))
    await sub
    assert result == [20, 30]
```

# Virtual time testing

Aioreactive also provides a virtual time event loop (`VirtualTimeEventLoop`) that enables you to write asyncio unit-tests that run in virtual time. Virtual time means that time is emulated, so tests run as quickly as possible even if they sleep or awaits long lived operations. A test using virtual time still gives the same result as it would have done if it had been run in real time.

For example the following test still gives the correct result even if it takes 0 seconds to run:

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_call_later():
    result = []

    def action(value):
        result.append(value)

    loop = asyncio.get_event_loop()
    loop.call_later(10, partial(action, 1))
    loop.call_later(1, partial(action, 2))
    loop.call_later(5, partial(action, 3))
    await asyncio.sleep(10)
    assert result == [2, 3, 1]
```

The `aioreactive.testing` module provides a test `Stream` that may delay sending values, and test `Listener` that records all events. These two classes helps you with testing in virtual time.

```python
@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_delay_done():
    xs = Stream()  # Test stream

    async def mapper(value):
        return value * 10

    ys = delay(0.5, xs)
    lis = Listener()  # Test listener
    sub = await listen(ys, lis)
    await xs.asend_later(0, 10)
    await xs.asend_later(1, 20)
    await xs.aclose_later(1)
    await sub

    assert lis.values == [
        (0.5, 10),
        (1.5, 20),
        (2.5,)
    ]
```

# Why not just use AsyncIterable for everything?

`AsyncIterable` and `AsyncSource` are closely related (in fact they are duals). `AsyncIterable` is an async iterable (pull) world, while `AsyncSource` is an async reactive (push) based world. There are many operations such as `map()` and `filter()` that may be simpler to implement using `AsyncIterable`, but once we start to include time, then `AsyncSource` really starts to shine. Operators such as `delay()` makes much more sense for `AsyncSource` than for `AsyncIterable`.

# Will aioreactive replace RxPY?

Aioreactive will not replace [RxPY](https://github.com/ReactiveX/RxPY). RxPY is an implementation of `Observable`. Aioreactive however lives within the `AsyncObservable` dimension.

Rx and RxPY has hundreds of different query operators, and we have no plans to implementing all of those for aioreactive.

Many ideas from aioreactive might be ported back into RxPY, and the goal is that RxPY one day may be built on top of aioreactive.

# References

Aioreactive was inspired by:

* [Is it really Pythonic to continue using linq operators instead of plain old functions?](https://github.com/ReactiveX/RxPY/issues/94)
* [Reactive Extensions (Rx)](http://reactivex.io) and [RxPY](https://github.com/ReactiveX/RxPY).
* [Underscore.js](http://underscorejs.org).
* [itertools](https://docs.python.org/3/library/itertools.html) and [functools](https://docs.python.org/3/library/functools.html).
* [dbrattli/OSlash](https://github.com/dbrattli/OSlash)
* [kriskowal/q](https://github.com/kriskowal/q).

# License

The MIT License (MIT)
Copyright (c) 2016 Børge Lanes, Dag Brattli.
