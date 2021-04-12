class TestedRule:
    def __init__(self, rule, result):
        """Represents a row in the results_scans table"""
        self.__rule   = rule
        self.__result = result

    def __str__(self):
        return 'Title:\t%s\nRule:\t%s\nResult:\t%s' % (self.title(), self.slug(), self.result())

    def title(self):
        return self.__rule.title()

    def slug(self):
        return self.__rule.slug()

    def result(self):
        return self.__result.value()

    def id(self):
        return self.__rule.id()

    def setId(self, id):
        self.__rule.setId(id)
