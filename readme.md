EZmap - make python parallel mapping even simpler
=================================================

I was always finding myself writing snippets around parallel mapping in python,
such as making partial functions and checking if the code should work in
parallel mode or sequentially. 

So that I wrote this package to make my life easier. Everything goes through the
same command: `map`!

Despite the `Pool` class from the multiprocessing package is quite nice, in this
module, I implemented a `map` that remedies to its lack of progress indicator,
based on Valentin Haenel's progress bar package (included).

(progress-bar source: https://code.google.com/p/python-progressbar/)


Content
-------

**map**
Equivalent of `map()` builtin which takes a ncpu keywords and can show a
progressbar during the computations.

Note: lambda functions are cast to __PicklableLambda__

Example:

    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs
    >>> print map(partial(fn, a=1, c=2, b=2, allkeywords=True), (3, 4, 5), ncpu=-1)
    [(1, 2, (3,), {'c': 2}), (1, 2, (4,), {'c': 2}), (1, 2, (5,), {'c': 2})]



**map_async**
Asynchronous equivalent of `map()` which returns a result object.


**Partial**
function class that mimics the `functools.partial` behavior but makes sure it
stays __picklable__.  The new function is a partial application of the given
arguments and keywords.  The remaining arguments are sent at the end of the
fixed arguments.  Unless you set the `allkeywords` option, which gives more
flexibility to the partial definition.

see: `allkeywords` 

Note: lambda functions are cast to __PicklableLambda__

Example:

    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs
    >>> print partial(fn, 2, c=2)(3, 4, 5, 6, 7)
    # TypeError: __call__() takes exactly 2 arguments (6 given)
    >>> print partial(fn, 2, c=2)(3)
    (3, 2, (), {'c': 2})
    >>> print partial(fn, a=1, c=2, b=2, allkeywords=True)(3, 4, 5, 6, 7)
    >>> print partial(fun, a=1, b=2)(3, 4, 5, 6, 7, c=3)


**allkeywords**
Decorator that allows any argument to be set as a keyword. Especially useful
for partial function definitions

Example:

    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs
    >>> print partial(_allkeywords(fn), a=1, c=2, b=2)(3, 4, 5, 6, 7)
    # normally: TypeError but works now



**PicklableLambda**
Class/Decorator that ensures a lambda ("anonymous" function) will be picklable.
Lambda are not picklable because they are anonymous while pickling mainly works
with the names.  This class digs out the code of the lambda, which is picklable
and recreates the lambda function when called.  The encapsulated lambda is not
anonymous anymore.

Notes:
* Dependencies are not handled.
* Often Partial can replace a lambda definition
* map, map_async, Partial from this package automatically cast lambda functions
to PicklableLambda.

Example:

        >>> f = lambda *args, **kwargs: (args, kwargs)
        >>> map(PicklableLambda(f), (10, 11), ncpu=-1)
        [((10,), {}), ((11,), {})]
