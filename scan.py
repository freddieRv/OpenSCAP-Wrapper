class Scan:
    def __init__(self, args={}):
        self.__rules = {}
        self.__id    = args.get('id', None)
        self.__slug  = args.get('slug', None)

    def summaryStr(self):
        results     = {}
        total       = len(self.__rules)
        summary_str = '\ttotal:\t%d\n' % (total)

        for rule in self.__rules.values():
            results[rule.result()] = results.get(rule.result(), 0) + 1

        for result in results.keys():
            summary_str += '\t%s: %s\n' % (result, results[result])

        return summary_str

    def addTestedRule(self, rule):
        self.__rules[rule.slug()] = rule

    def rules(self):
        return self.__rules.values()

    def id(self):
        return self.__id

    def slug(self):
        return self.__slug

    def getRuleBySlug(self, slug):
        return self.__rules.get(slug, None)

    def _rulesWithResult(self, result):
        return [rule for rule in self.rules() if rule.result() == result]

    def __str__(self):
        out = ""
        for r in self.__rules.values():
            out += str(r) + '\n\n'

        out += self.summaryStr()
        return out
