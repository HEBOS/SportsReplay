"""
LINQ analog for Python
Contact: purin.anton@gmail.com
"""
__author__ = 'Anton Purin'
import itertools


class Linq(object):
    """Allows to apply LINQ-like methods to wrapped iterable"""

    class LinqException(Exception):
        """
        Special exception to be thrown by Linq
        """
        pass

    def __init__(self, iterable):
        """
        Instantiates Linq wrapper
        :param iterable: iterable to wrap
        """
        if iterable is None:
            raise Linq.LinqException("iterable is None")
        if iterable.__class__ is Linq:
            self.iterable = iterable.iterable
        else:
            self.iterable = iterable

    def __repr__(self):
        return repr(self.to_list())

    def __iter__(self):
        """
        Allows to iterate Linq object
        """
        return iter(self.iterable)

    def any(self, predicate=None):
        """
        Returns true if there any item which matches given predicate.
        If no predicate given returns True if there is any item at all.
        :param predicate: Function which takes item as argument and returns bool
        :returns: Boolean
        :rtype: bool
        """
        for i in self.iterable:
            if predicate is None:
                return True
            elif predicate(i):
                return True
        return False

    def all(self, predicate):
        """
        Returns true if all items match given predicate.
        :param predicate: Function which takes item as argument and returns bool
        :returns: Boolean
        :rtype: bool
        """
        for i in self.iterable:
            if not predicate(i):
                return False
        return True

    def first(self, predicate=None):
        """
        Returns first item which matches predicate or first item if no predicate given.
        Raises exception, if no matching items found.
        :param predicate: Function which takes item as argument and returns bool
        :returns: item
        :rtype: object
        """
        for i in self.iterable:
            if predicate is None:
                return i
            elif predicate(i):
                return i
        raise Linq.LinqException('No matching items!')

    def first_or_none(self, predicate=None):
        """
        Returns first item which matches predicate or first item if no predicate given.
        Returns None, if no matching items found.
        :param predicate: Function which takes item as argument and returns bool
        :returns: item
        :rtype: object
        """
        try:
            return self.first(predicate)
        except Linq.LinqException:
            return None

    def last(self, predicate=None):
        """
        Returns last item which matches predicate or last item if no predicate given.
        Raises exception, if no matching items found.
        :param predicate: Function which takes item as argument and returns bool
        :returns: item
        :rtype: object
        """
        last_item = None
        last_item_set = False
        for i in self.iterable:
            if (predicate is not None and predicate(i)) or (predicate is None):
                last_item = i
                last_item_set = True

        if not last_item_set:
            raise Linq.LinqException('No matching items!')
        return last_item

    def last_or_none(self, predicate=None):
        """
        Returns last item which matches predicate or last item if no predicate given.
        Returns None, if no matching items found.
        :param predicate: Function which takes item as argument and returns bool
        :returns: item
        :rtype: object
        """
        try:
            return self.last(predicate)
        except Linq.LinqException:
            return None

    def to_list(self):
        """
        Converts LinqIterable to list
        :returns: list
        :rtype: list
        """
        return list(self.iterable)

    def to_dictionary(self, key_selector=None, value_selector=None, unique=True):
        """
        Converts LinqIterable to dictionary
        :param key_selector: function which takes item and returns key for it
        :param value_selector: function which takes item and returns value for it
        :param unique: boolean, if True that will throw exception if keys are not unique
        :returns: dict
        :rtype: dict
        """
        result = {}
        keys = set() if unique else None

        for i in self.iterable:
            key = key_selector(i) if key_selector is not None else i
            value = value_selector(i) if value_selector is not None else i
            if unique:
                if key in keys:
                    raise Linq.LinqException("Key '" + repr(key) + "' is used more than once.")
                keys.add(key)
            result[key] = value
        return result

    def where(self, predicate):
        """
        Returns items which matching predicate function
        :param predicate: Function which takes item as argument and returns bool
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        return Linq([i for i in self.iterable if predicate(i)])

    def distinct(self, key_selector=None):
        """
        Filters distinct values from enumerable
        :param key_selector: function which takes item and returns key for it
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        key_selector = key_selector if key_selector is not None else lambda item: item
        keys = set()
        return Linq([i for i in self.iterable if key_selector(i) not in keys and not keys.add(key_selector(i))])

    def group_by(self, key_selector=None, value_selector=None):
        """
        Groups given items by keys.
        :param key_selector: function which takes item and returns key for it
        :param value_selector: function which takes item and returns value for it
        :returns: Dictionary, where value if Linq for given key
        :rtype: dict
        """
        key_selector = key_selector if key_selector is not None else lambda item: item
        value_selector = value_selector if value_selector is not None else lambda item: item

        result = {}
        for i in self.iterable:
            key = key_selector(i)
            if result.__contains__(key):
                result[key].append(value_selector(i))
            else:
                result[key] = [value_selector(i)]
        for key in result:
            result[key] = Linq(result[key])
        return result

    def order_by(self, value_selector=None, comparer=None, descending=False):
        """
        Orders items.
        :param value_selector: function which takes item and returns value for it
        :param comparer: function which takes to items and compare them returning int
        :param descending: shows how items will be sorted
        """
        return Linq(sorted(self.iterable, comparer, value_selector, descending))

    def take(self, number):
        """
        Takes only given number of items, of all available items if their count is less than number
        :param number: number of items to get
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        def internal_take(iterable, number):
            count = 0
            for i in iterable:
                count += 1
                if count > number:
                    break
                yield i

        return Linq(internal_take(self.iterable, number))

    def skip(self, number):
        """
        Skips given number of items in enumerable
        :param number: number of items to get
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        def internal_skip(iterable, number):
            count = 0
            for i in iterable:
                count += 1
                if count <= number:
                    continue
                yield i

        return Linq(internal_skip(self.iterable, number))

    def select(self, selector):
        """
        Converts items in list with given function
        :param selector: Function which takes item and returns other item
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        return Linq([selector(i) for i in self.iterable])

    def select_many(self, selector):
        """
        Converts items in list with given function
        :param selector: Function which takes item and returns iterable
        :returns: results wrapped with Linq
        :rtype: Linq
        """
        return Linq([i for i in [selector(sub) for sub in self.iterable]])

    def foreach(self, func):
        """
        Allows to perform some action for each object in iterable, but not allows to redefine items
        :param func: Function which takes item as argument
        :returns: self
        :rtype: Linq
        """
        for i in self.iterable:
            func(i)
        return self

    def concat(self, iterable):
        """
        Concats two iterables
        :param iterable: Any iterable
        :returns: self
        :rtype: Linq
        """
        return Linq(itertools.chain(self.iterable, iterable))

    def concat_item(self, item):
        """
        Concats iterable with single item
        :param item: Any item
        :returns: self
        :rtype: Linq
        """
        return Linq(itertools.chain(self.iterable, [item]))

    def except_for(self, iterable):
        """
        Filters items except given iterable
        :param iterable: Any iterable
        :returns: self
        :rtype: Linq
        """
        return Linq([i for i in self.iterable if i not in iterable])

    def intersect(self, iterable):
        """
        Intersection between two iterables
        :param iterable: Any iterable
        :returns: self
        :rtype: Linq
        """
        return Linq([i for i in self.iterable if i in iterable])