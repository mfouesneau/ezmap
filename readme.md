EZmap - make python parallel mapping even simpler
=================================================

I was always finding myself writing snippets around parallel mapping in python, such as making partial functions and checking if the code should work in parallel mode or sequentially. 

So that I wrote this package to make my life easier. Everything goes through the same command: `map`!

Despite the `Pool` class from the multiprocessing package is quite nice, in this module, I implemented a `map` that remedies to its lack of progress indicator, based on Valentin Haenel's progress bar package (included).

(progress-bar source: https://code.google.com/p/python-progressbar/)


This package has been tested with both Python 2.7 and Python 3


Content
-------

**map**

Equivalent of `map()` builtin which takes a ncpu keywords and can show a progressbar during the computations.

Note: lambda functions are cast to __PicklableLambda__

Example:

```python
>>> def fn(a, b, *args, **kwargs):
	return a, b, args, kwargs
>>> print map(partial(fn, a=1, c=2, b=2, allkeywords=True), (3, 4, 5), ncpu=-1)
[(1, 2, (3,), {'c': 2}), (1, 2, (4,), {'c': 2}), (1, 2, (5,), {'c': 2})]
```


**map_async**

Asynchronous equivalent of `map()` which returns a result object.


**Partial**

Function class that mimics the `functools.partial` behavior but makes sure it stays __picklable__.  The new function is a partial application of the given arguments and keywords.  The remaining arguments are sent at the end of the fixed arguments.  Unless you set the `allkeywords` option, which gives more flexibility to the partial definition.

see: `allkeywords` 

Note: lambda functions are cast to __PicklableLambda__

Example:

```python
>>> def fn(a, b, *args, **kwargs):
	return a, b, args, kwargs
>>> print partial(fn, 2, c=2)(3, 4, 5, 6, 7)
# TypeError: __call__() takes exactly 2 arguments (6 given)
>>> print partial(fn, 2, c=2)(3)
(3, 2, (), {'c': 2})
>>> print partial(fn, a=1, c=2, b=2, allkeywords=True)(3, 4, 5, 6, 7)
>>> print partial(fun, a=1, b=2)(3, 4, 5, 6, 7, c=3)
```


**allkeywords**

Decorator that allows any argument to be set as a keyword. Especially useful for partial function definitions

Example:

```python
>>> def fn(a, b, *args, **kwargs):
	return a, b, args, kwargs
>>> print partial(_allkeywords(fn), a=1, c=2, b=2)(3, 4, 5, 6, 7)
# normally: TypeError but works now
```



**PicklableLambda**

Class/Decorator that ensures a lambda ("anonymous" function) will be picklable.  Lambda are not picklable because they are anonymous while pickling mainly works with the names.  This class digs out the code of the lambda, which is picklable and recreates the lambda function when called.  The encapsulated lambda is not anonymous anymore.

Notes:
* Dependencies are not handled.
* Often Partial can replace a lambda definition
* map, map_async, Partial from this package automatically cast lambda functions
to PicklableLambda.

Example:

```python
>>> f = lambda *args, **kwargs: (args, kwargs)
>>> map(PicklableLambda(f), (10, 11), ncpu=-1)
[((10,), {}), ((11,), {})]
```

**Pool**

Overloaded built-in class to make a context manager A process pool object which controls a pool of worker processes to which jobs can be submitted. It supports asynchronous results with timeouts and callbacks and has a parallel map implementation.

```python
Example
>>> with Pool(10) as p:
	p.map(func, seq)
```

**async**

Decorator function which makes the decorated function run in a separate Process (asynchronously).  Returns the created Process object.

Making async tasks in python is easy. However making async tasks returning values is a pain in the neck due to limitations in Python's pickling machinery. The trick is to wraps a top-level function around an asynchronous dispatcher.

when the decorated function is called, a task is submitted to a process pool, and a future object is returned, providing access to an eventual return value.

The future object has a blocking get() method to access the task result: it will return immediately if the job is already done, or block until it completes.

This decorator won't work on methods, due to limitations in Python's pickling machinery (in principle methods could be made pickleable, but good luck on that).

You can also use a common pool to handle multiple async tasks. However, keep in mind that the pool must be generated in the main level.  

Example:

```python
>>> @async_with_pool(Pool(3))
def task1():
	do_something

>>> t1 = task1()
>>> t1.join()
```
Example:

```python

>>> @async
    def printsum(uid, values):
        summed = 0
        for value in values:
            #_time.sleep(0.1)
            summed += value

        print("Worker %i: sum value is %i" % (uid, summed))

        return (uid, summed)

>>> from random import sample
>>> pool = Pool(4)
>>> async.pool = pool
>>> p = range(0, 1000)
>>> results = []
>>> for i in range(4):
        result = printsum(i, sample(p, 100))
        results.append(result)

>>> for result in results:
        print("Worker %i: sum value is %i" % result.get())
```
