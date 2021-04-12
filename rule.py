class Rule:
    def __init__(self, args={}):
        """Represents a row in the rules table"""
        self.__id    = args.get('id', None)
        self.__title = args.get('title', None)
        self.__slug  = args.get('slug', None)

    def __str__(self):
        return 'Title:\t%s\nRule:\t%s' % (self.__title, self.__slug)

    def title(self):
        return self.__title

    def slug(self):
        return self.__slug

    def id(self):
        return self.__id

    def setId(self, id):
        self.__id = id
