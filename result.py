class Result:
    """Represents a row in the results table"""
    def __init__(self, args):
        self.__id    = args.get('id', None)
        self.__value = args.get('value', None)

    def value(self):
        return self.__value

    def id(self):
        return self.__id
