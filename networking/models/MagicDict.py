from collections import OrderedDict


class MagicDict(OrderedDict):
    def __init__(self, ordered_dict, required_keys, optional_keys):
        """
        Initializes a magic dict instance. This method is similar to the OrderedDict constructor, but it also
        verifies all keys we expect in the data are there and adds any optional ones into the data as None.
        :param ordered_dict: The ordered dictionary we'd like to format
        :param required_keys: The keys we expect to be in the dictionary
        :param optional_keys: The keys we want to be in the dictionary, but might not be
        """
        super().__init__(ordered_dict)

        self.__verify(required_keys)
        self.__fill(optional_keys)

    def __verify(self, required_keys):
        """
        Verifies all the keys we expect are in the dictionary.
        :param required_keys: The keys we expect are going to be in the dictionary
        """
        keys = set(self.keys())
        required_keys = set(required_keys)

        if not required_keys <= keys:
            missing_keys = required_keys - keys
            raise KeyError('Missing required keys: ' + str(missing_keys))

    def __fill(self, optional_keys):
        """
        Fills the dictionary with any optional keys that might not be included initially. This helps for differentiating
        subclasses down the deserialization pipeline.
        :param optional_keys: The optional keys we want, but don't need, in the dictionary
        """
        for optional_key in optional_keys:
            if optional_key not in self:
                self[optional_key] = None

    def cleaned(self):
        """
        Take that semi-complete xmltodict result and turn it into a full-fledged JSON-esque result.
        :return: The OrderedDict, recursively converted to standard library dictionaries and lists
        """
        copy = dict(self)
        for key in copy:
            MagicDict.__to_dict_conversion(copy[key], copy, key)
        return copy

    @staticmethod
    def clean(d):
        """
        Take that semi-complete xmltodict result and turn it into a full-fledged JSON-esque result, now without the
        MagicDict instance.
        :param d: The OrderedDict to clean
        :return: The OrderedDict, recursively converted to standard library dictionaries and lists
        """
        if not isinstance(d, OrderedDict):
            return d

        d = dict(d)

        for key in d:
            MagicDict.__to_dict_conversion(d[key], d, key)

        return d

    @staticmethod
    def __to_dict_conversion(raw, parent=None, key=None):
        """
        This method recursively converts contents of an OrderedDict into dictionaries and lists. It's called from
        the clean and cleaned methods in the magic dict class.
        :param raw: The raw data to convert
        :param parent: The parent dictionary of the raw data
        :param key: The key of our raw data in the parent dictionary
        """
        if not isinstance(raw, OrderedDict):
            return
        if 'item' in raw:
            parent[key] = raw['item']
            if isinstance(parent[key], OrderedDict):
                parent[key] = [parent[key]]
            for i, child in enumerate(parent[key]):
                MagicDict.__to_dict_conversion(parent[key][i], parent[key], i)
        else:
            parent[key] = dict(raw)
            for child_key in parent[key]:
                MagicDict.__to_dict_conversion(parent[key][child_key], parent[key], child_key)

