from abc import ABC, abstractmethod
import subprocess
import argparse
from testedrule import TestedRule
from scan import Scan
from result import Result
from rule import Rule

SUCCESS = 0
ERROR   = 1

class Command(ABC):
    """Interface to be implemented by concrete commands"""
    def __init__(self, scan_manager):
        self._errors   = []
        self._smanager = scan_manager
        self._args     = None

    def ready(self):
        """Validate command params if needed"""
        return True

    @abstractmethod
    def exec(self):
        """Actually execute command"""
        if not ready():
            return ERROR

    @abstractmethod
    def output(self):
        """Return the output of the command"""
        pass

    def errors(self):
        """Return a list of errors generated on params validation or execution"""
        return self._errors

    @staticmethod
    def addArguments(parser):
        """Add own arguments to given parser object"""
        pass

    def _addError(self, error):
        """Adds an error to the internal error list"""
        self._errors.append(error)

    @staticmethod
    def helpStr():
        """Return a small description of what the command does"""
        return ''


class ScanCommand(Command):
    def __init__(self, scan_manager, args):
        super().__init__(scan_manager)
        self.__xccdf_file = args.get('xccdf-file', None)
        self.__cpe_file   = args.get('cpe-file', None)
        self.__scan       = None

    @staticmethod
    def helpStr():
        return 'Perform evaluation driven by XCCDF file (stig profile)'

    @staticmethod
    def addArguments(parser):
        parser.add_argument("xccdf-file", help="The XCCDF file to be used", type=argparse.FileType('r'))
        parser.add_argument(
            "--cpe",
            help="Use given cpe dictionary or language (autodetected) for applicability checks",
            dest='cpe-file',
            type=argparse.FileType('r')
        )

    def ready(self):
        am_i_ready = (self.__xccdf_file is not None)

        if not am_i_ready:
            self._addError("No XCCDF file")

        return am_i_ready

    def _commandParams(self):
        params = [
            "oscap",
            "xccdf",
            "eval",
            "--profile",
            "stig",
        ]

        if self.__cpe_file is not None:
            params.append("--cpe")
            params.append(self.__cpe_file.name)

        params.append(self.__xccdf_file.name)

        return params

    def exec(self):
        if not self.ready():
            return ERROR

        self.__scan = Scan()

        process = subprocess.run(
            self._commandParams(),
            # ["cat", "scan.out"],
            # ["echo"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if process.returncode != SUCCESS:
            self._addError(process.stderr)

        excode = process.returncode

        self.__parseOutput(process.stdout)

        if len(self.__scan.rules()) > 0:
            self._smanager.saveScan(self.__scan)
        else:
            self.__scan = None
            self._addError('No rules tested, discarding scan. Check xccdf file validity')
            excode = ERROR

        return excode

    def __parseOutput(self, cmdout):
        aux_buff = cmdout.decode().split('\n\n')

        for rule in aux_buff:
            current_rule = {}
            rule_attr    = rule.split('\n')

            if len(rule_attr) == 3:
                for attr in rule_attr:
                    splitted_attr = attr.split('\r\t')
                    if len(splitted_attr) == 2:
                        if splitted_attr[0] == 'Title':
                            current_rule['title'] = splitted_attr[1]
                        elif splitted_attr[0] == 'Rule':
                            current_rule['slug'] = splitted_attr[1]
                        elif splitted_attr[0] == 'Result':
                            current_rule['value'] = splitted_attr[1]
                            rule   = Rule(current_rule)
                            result = Result(current_rule)
                            self.__scan.addTestedRule(TestedRule(rule, result))
                            current_rule = {}

    def output(self):
        outp = 'Couldn\'t perform scan'

        if self.__scan is not None:
            outp = str(self.__scan)

        return outp

class HistoryCommand(Command):
    def __init__(self, scan_manager, args):
        super().__init__(scan_manager)
        self.__scans   = None

    @staticmethod
    def helpStr():
        return 'Show a list of the summaries of performed scans'

    def exec(self):
        if not self.ready():
            return ERROR
        self.__scans = self._smanager.getAllScans()
        return SUCCESS

    def output(self):
        out = ''

        if len(self.__scans) == 0:
            out = 'no scans'
        else:
            for scan in self.__scans:
                out += 'id: ' + scan.slug() + '\n' + scan.summaryStr() + '\n\n'

        return out

class ShowCommand(Command):
    def __init__(self, scan_manager, args):
        super().__init__(scan_manager)
        self.__scan_slug = args.get('scan-id', None)
        self.__scan      = None

    def ready(self):
        return self.__scan_slug is not None

    @staticmethod
    def helpStr():
        return 'Show the summary and the list of rules for a given scan id'

    @staticmethod
    def addArguments(parser):
        parser.add_argument("scan-id", help="ID of the scan to show")

    def exec(self):
        if not self.ready():
            return ERROR

        self.__scan = self._smanager.getScanBySlug(self.__scan_slug)

        excode = 0
        if self.__scan is None:
            excode = ERROR

        return excode

    def output(self):
        out = ''
        if self.__scan is None:
            if self.__scan_slug is not None:
                out = 'couldn\'t find scan with id %s' % self.__scan_slug
        else:
            out = str(self.__scan)

        return out

class CompareCommand(Command):
    def __init__(self, scan_manager, args):
        super().__init__(scan_manager)
        self.__scan_a_slug       = args.get('scan-a-id', None)
        self.__scan_b_slug       = args.get('scan-b-id', None)
        self.__scan_a            = None
        self.__scan_b            = None
        self.__mismatching_rules = []
        self.__fixed             = 0
        self.__introduced        = 0

    def ready(self):
        am_i_ready = True

        if None in (self.__scan_a_slug, self.__scan_b_slug):
            am_i_ready = False
            self._addError("Not enough arguments")
        elif self.__scan_a_slug == self.__scan_b_slug:
            am_i_ready = False
            self._addError("Given IDs are the same")

        return am_i_ready

    @staticmethod
    def helpStr():
        return 'Shows scans summaries, total fixed and introduced errors, and a list of mismatching results'

    def exec(self):
        if not self.ready():
            return ERROR

        excode = SUCCESS

        self.__scan_a = self._smanager.getScanBySlug(self.__scan_a_slug)
        self.__scan_b = self._smanager.getScanBySlug(self.__scan_b_slug)

        if self.__scan_a is None:
            self._addError('Couldn\'t find scan with id %s' % self.__scan_a_slug)
            excode = ERROR

        if self.__scan_b is None:
            self._addError('Couldn\'t find scan with id %s' % self.__scan_b_slug)
            excode = ERROR

        if excode == ERROR:
            return ERROR

        for rule_b in self.__scan_b.rules():
            rule_a = self.__scan_a.getRuleBySlug(rule_b.slug())

            if rule_a is not None:
                if rule_b.result() !=  rule_a.result():
                    self.__mismatching_rules.append((rule_b, rule_a))

                if rule_a.result() == 'pass' and rule_b.result() != 'pass':
                        self.__introduced += 1
                elif rule_b.result() == 'pass' and rule_a.result() != 'pass':
                        self.__fixed += 1

        return SUCCESS

    def output(self):
        outp = ''
        if self.__scan_a is not None and self.__scan_b is not None:
            total_mismatching = len(self.__mismatching_rules)
            outp += '>> %s\n%s' % (self.__scan_a.slug(), self.__scan_a.summaryStr())
            outp += '\n\n'
            outp += '>> %s\n%s' % (self.__scan_b.slug(), self.__scan_b.summaryStr())
            outp += '\n\n'
            outp += 'Fixed in %s: %s' % (self.__scan_b.slug(), self.__fixed)
            outp += '\n'
            outp += 'Introduced in %s: %s' % (self.__scan_b.slug(), self.__introduced)
            outp += '\n\n'
            outp += 'Total mismatching rules: %s\n\n' % (total_mismatching)

            if total_mismatching > 0:
                outp += 'Mismatching rules summary:\n\n'

        for rule_a, rule_b in self.__mismatching_rules:
            values = (
                rule_a.title(),
                rule_a.slug(),
                self.__scan_a.slug(),
                rule_a.result(),
                self.__scan_b.slug(),
                rule_b.result()
            )
            outp += 'Title:\t%s\nRule:\t%s\nResult:\n\t%s: %s\n\t%s: %s\n\n' % values

        return outp

    @staticmethod
    def addArguments(parser):
        parser.add_argument('scan-a-id', help="ID of the scan to compare with")
        parser.add_argument('scan-b-id', help="ID of the scan to compare against")

COMMANDS = {
    'scan':    ScanCommand,
    'history': HistoryCommand,
    'show':    ShowCommand,
    'compare': CompareCommand
}
