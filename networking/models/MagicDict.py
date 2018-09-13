from collections import OrderedDict


class MagicDict(OrderedDict):
    def __init__(self, ordered_dict, required_keys, optional_keys):
        super().__init__(ordered_dict)

        self.__verify(required_keys)
        self.__fill(optional_keys)

    def __verify(self, required_keys):
        keys = set(self.keys())
        required_keys = set(required_keys)
        if not required_keys <= keys:
            missing_keys = required_keys - keys
            raise KeyError('Missing required keys: ' + missing_keys)

    def __fill(self, optional_keys):
        for optional_key in optional_keys:
            if optional_key not in self:
                self[optional_key] = None

    def cleaned(self):
        copy = dict(self)
        for key in copy:
            MagicDict.__to_dict_conversion(copy[key], copy, key)
        return copy

    @staticmethod
    def clean(d):
        if not isinstance(d, OrderedDict):
            return d
        d = dict(d)
        for key in d:
            MagicDict.__to_dict_conversion(d[key], d, key)

    @staticmethod
    def __to_dict_conversion(raw, parent=None, key=None):
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

