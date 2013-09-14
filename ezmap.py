"""
This package is meant to mimic a regular map call with different parallel
processing handling: built-in map, multiprocessing with given number of cpus,
etc. It also provides the multiprocessing.map_async with a similar calling
sequence.

Example:

    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs

    >>> print map(partial(fn, a=1, c=2, b=2, allkeywords=True), (3, 4, 5), ncpu=-1)
    [(1, 2, (3,), {'c': 2}), (1, 2, (4,), {'c': 2}), (1, 2, (5,), {'c': 2})]
"""
import multiprocessing as _mp
import functools as _fntools
import inspect as _inspect
import time
from progressbar import PBar
from multiprocessing.pool import Pool as _Pool


__all__ = ['map', 'map_async', 'Partial', 'allkeywords',
           'PicklableLambda', 'async', 'async_with_pool']

#keep the built-in function
_map = map


def map(func, iterable, chunksize=None, ncpu=0, limit=True, progress=False):
    """
    Equivalent of `map()` builtin

    Note: lambda functions are cast to PicklableLambda

    Parameters
    ----------

    func: callable
        function to be mapped over an iterable.

    iterable: iterable or generator
        args can be any iterable object. Func will be called over each item.

    chunksize: int (default None, i.e., equal repartition)
        number of items per cpu. Default is equal repartition.
        it chops the iterable into a number of chunks which it submits to the
        process pool as separate tasks. The (approximate) size of these chunks
        can be specified by setting chunksize to a positive integer.

    ncpu: int (default 0, i.e, built-in map behavior)
        number of cpu to use for the mapping.
        0 is equivalent to calling the built-in map function
        <0 is equivalent to requesting all cpus

    limit: bool (default True)
        if ncpu is greater than the number of available cpus, setting this
        keyword will limit the request to the maximum available

        Note: sometimes the os load controller does awesome and some speed-up
        could be obtained when requesting more cpus than available

    progress: bool (default False)
        if set display a progressbar

    Outputs
    -------
        return an iterable of individual results
    """
    if (ncpu == 0):
        if (not progress):
            return _map(func, iterable)
        else:
            n = len(iterable)
            r = []
            if isinstance(progress, str):
                txt = progress
            else:
                txt = func.__name__
            with PBar(n, txt=txt) as pb:
                for e, k in enumerate(iterable):
                    r.append(func(k))
                    pb.update(e)
            return r
    elif progress:
        _n = _mp.cpu_count()
        if (ncpu <= 0):
            # use all available cpus
            p = _mp.Pool(_n)
        elif (ncpu > _n) & (limit is True):
            p = _mp.Pool(_n)
        else:
            p = _mp.Pool(ncpu)

        if not hasattr(iterable, '__len__'):
            iterable = list(iterable)
        ntasks = len(iterable)

        if isinstance(progress, str):
            txt = progress
        else:
            txt = func.__name__

        with PBar(ntasks, txt=txt) as pb:
            # get the pool working asynchronously
            if islambda(func):
                amap = p.map_async(PicklableLambda(func), iterable, chunksize)
            else:
                amap = p.map_async(func, iterable, chunksize)
            left = 1
            while left > 0:
                time.sleep(0.1)
                left = amap._number_left
                pb.update(ntasks - left)
        return amap.get()
    else:
        return map_async(func, iterable, chunksize, ncpu=ncpu, limit=limit).get()


def map_async(func, iterable, chunksize=None, callback=None, ncpu=0, limit=True):
    """
    Asynchronous equivalent of `map()` builtin
    A variant of the map() method which returns a result object.

    Note: lambda functions are cast to PicklableLambda

    Parameters
    ----------

    func: callable
        function to be mapped over an iterable.

    iterable: iterable or generator
        args can be any iterable object. Func will be called over each item.

    chunksize: int (default None, i.e., equal repartition)
        number of items per cpu. Default is equal repartition.
        it chops the iterable into a number of chunks which it submits to the
        process pool as separate tasks. The (approximate) size of these chunks
        can be specified by setting chunksize to a positive integer.

    callback: callable
        If callback is specified then it should be a callable which accepts a
        single argument. When the result becomes ready callback is applied to
        it (unless the call failed). callback should complete immediately since
        otherwise the thread which handles the results will get blocked.

    ncpu: int (default 0, i.e, built-in map behavior)
        number of cpu to use for the mapping.
        0 is equivalent to calling the built-in map function
        <0 is equivalent to requesting all cpus

    limit: bool (default True)
        if ncpu is greater than the number of available cpus, setting this
        keyword will limit the request to the maximum available

        Note: sometimes the os load controller does awesome and some speed-up
        could be obtained when requesting more cpus than available

    Outputs
    -------
        return an asynchrone descriptor
    """
    _n = _mp.cpu_count()
    if (ncpu <= 0):
        # use all available cpus
        p = _mp.Pool(_n)
    elif (ncpu > _n) & (limit is True):
        p = _mp.Pool(_n)
    else:
        p = _mp.Pool(ncpu)

    if islambda(func):
        return p.map_async(PicklableLambda(func), iterable, chunksize, callback)
    else:
        return p.map_async(func, iterable, chunksize, callback)


class Partial(object):
    """
    Partial(func, *args, **keywords) - function class that mimics the
    functools.partial behavior but makes sure it stays picklable.
    The new function is a partial application of the given arguments and
    keywords.  The remaining arguments are sent at the end of the fixed
    arguments.  Unless you set the allkeywords option, which gives more
    flexibility to the partial definition.

    Note: lambda functions are cast to PicklableLambda

    Parameters
    ----------
        func: callable
            the function from which the partial application will be made
        *args: tuple
            arguments to fix during the call
        **kwargs: dict
            keywords to the function call

        If 'allkeywords' keyword is set (default False) when defining the
        partial function or in a later call, it allows you to specify arguments
        and keywords in any order as traditional keywords. The remaining
        variables will be used to fill the blanks

    Outputs:
    ---------
        returns a callable function with preserved/wrapped documentation names etc.

    Example:
    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs

    >>> print partial(fn, 2, c=2)(3, 4, 5, 6, 7)
    # TypeError: __call__() takes exactly 2 arguments (6 given)
    >>> print partial(fn, 2, c=2)(3)
    (3, 2, (), {'c': 2})
    >>> print partial(fn, a=1, c=2, b=2, allkeywords=True)(3, 4, 5, 6, 7)
    >>> print partial(fun, a=1, b=2)(3, 4, 5, 6, 7, c=3)
    """
    def __init__(self, func, *args, **kwargs):

        if islambda(func):
            self.func = PicklableLambda(func)
        else:
            self.func = func
        self.args = args
        self.kwargs = kwargs
        _fntools.update_wrapper(self, func)

    def __repr__(self):
        return 'Partial({}), args={}, kwargs={}\n'.format(self.func.__name__, self.args, self.kwargs) + object.__repr__(self)

    def __call__(self, *fargs, **fkeywords):
        newkeywords = self.kwargs.copy()
        newkeywords.update(fkeywords)
        if newkeywords.get('allkeywords', False):
            newkeywords.pop('allkeywords')
            return allkeywords(self.func)(*(self.args + fargs), **newkeywords)
        else:
            return self.func(*(self.args + fargs), **newkeywords)


def allkeywords(f):
    """
    Decorator that allows any argument to be set as a keyword. Especially
    useful for partial function definitions

    Example:
    >>> def fn(a, b, *args, **kwargs):
           return a, b, args, kwargs

    >>> print partial(_allkeywords(fn), a=1, c=2, b=2)(3, 4, 5, 6, 7)
    # normally: TypeError but works now
    """
    @_fntools.wraps(f)
    def wrapper(*a, **k):
        a = list(a)
        for idx, arg in enumerate(_inspect.getargspec(f).args, -_inspect.ismethod(f)):  # or [0] in 2.5
            if arg in k:
                if idx < len(a):
                    a.insert(idx, k.pop(arg))
                else:
                    break
        return f(*a, **k)
    return wrapper


def islambda(func):
    """ Test if the function func is a lambda ("anonymous" function) """
    return getattr(func, 'func_name', False) == '<lambda>'


class PicklableLambda(object):
    """ Class/Decorator that ensures a lambda ("anonymous" function) will be
    picklable.
    Lambda are not picklable because they are anonymous while
    pickling mainly works with the names.  This class digs out the code of the
    lambda, which is picklable and recreates the lambda function when called.
    The encapsulated lambda is not anonymous anymore.

    Notes:
        * Dependencies are not handled.
        * Often Partial can replace a lambda definition
        * map, map_async, Partial from this package automatically cast lambda
          functions to PicklableLambda.

    Example:
        >>> f = lambda *args, **kwargs: (args, kwargs)
        >>> map(PicklableLambda(f), (10, 11), ncpu=-1)
        [((10,), {}), ((11,), {})]
    """
    def __init__(self, func):
        if not islambda(func):
            raise TypeError('Object not a lambda function')
        self.func_code = _inspect.getsource(func)
        self.__name__ = self.func_code.split('=')[0].strip()

    def __repr__(self):
        return self.func_code + object.__repr__(self)

    def __call__(self, *args, **kwargs):
        func = eval(self.func_code.split('=')[1])
        return func(*args, **kwargs)


def async(func):
    """
    decorator function which makes the decorated function run in a separate
    Process (asynchronously).  Returns the created Process object.

    Example:

    >>> @async
        def task1():
            do_something

    >>> t1 = task1()
    >>> t1.join()
    """
    if islambda(func):
        _func = PicklableLambda(func)
    else:
        _func = func

    @_fntools.wraps(_func)
    def async_func(*args, **kwargs):
        func_hl = _mp.Process(target=_func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def async_with_pool(pool):
    """
    decorator function which makes the decorated function run in a separate
    Process (asynchronously).  Returns the created Process object.

    Example:

    >>> @async_with_pool(Pool(3))
        def task1():
            do_something

    >>> t1 = task1()
    >>> t1.join()
    """
    if not hasattr(pool, 'Process'):
        raise AttributeError('pool object is expected to have a Process attribute')

    def deco(func):
        if islambda(func):
            _func = PicklableLambda(func)
        else:
            _func = func

        @_fntools.wraps(_func)
        def async_func(*args, **kwargs):
            func_hl = pool.Process(target=_func, args=args, kwargs=kwargs)
            func_hl.start()
            return func_hl

        return async_func
    return deco


class Pool(_Pool):
    """ Overloadind the built-in class to make a context manager
    A process pool object which controls a pool of worker processes to
    which jobs can be submitted. It supports asynchronous results with
    timeouts and callbacks and has a parallel map implementation.
    """
    def __init__(self, ncpu, initializer=None, initargs=(),
                 maxtasksperchild=None, limit=True):
        """
        INPUTS
        ------
        ncpu: int (default 0, i.e, built-in map behavior)
            number of cpu to use for the mapping.
            0 is equivalent to calling the built-in map function
            <0 is equivalent to requesting all cpus

        initializer: callable
            if set, each worker process will call initializer(*initargs) when
            it starts.

        initargs: tuple
            arguments to use with the initializer

        maxtasksperchild: int
            number of tasks a worker process can complete before it will exit
            and be replaced with a fresh worker process, to enable unused
            resources to be freed. The default maxtasksperchild is None, which
            means worker processes will live as long as the pool.

        limit: bool (default True)
            if ncpu is greater than the number of available cpus, setting this
            keyword will limit the request to the maximum available

            Note: sometimes the os load controller does awesome and some speed-up
            could be obtained when requesting more cpus than available
        """
        _n = _mp.cpu_count()
        if (ncpu <= 0):
            # use all available cpus
            _Pool.__init__(self, processes=_n, initializer=initializer,
                           initargs=initargs,
                           maxtasksperchild=maxtasksperchild)
        elif (ncpu > _n) & (limit is True):
            _Pool.__init__(self, processes=_n, initializer=initializer,
                           initargs=initargs,
                           maxtasksperchild=maxtasksperchild)
        else:
            _Pool.__init__(self, processes=ncpu, initializer=initializer,
                           initargs=initargs,
                           maxtasksperchild=maxtasksperchild)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
