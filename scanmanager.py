import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from testedrule import TestedRule
from scan import Scan
from rule import Rule
from result import Result

class ScanManager:
    def __init__(self, args):
        self.__cursor = None
        self.__error  = ''
        self.__mysql_templates = {
            'insert_rule_result':    'INSERT INTO rules_scans (scan_id, rule_id, result_id) VALUES (%s, %s, %s)',
            'select_all_scans':      'SELECT * FROM scans',
            'fetch_scan_by_slug':    'SELECT * FROM scans WHERE slug = %s',
            'fetch_result_by_value': 'SELECT * FROM results WHERE value = %s',
            'insert_scan':           'INSERT INTO scans (slug) VALUES (%s)',
            'insert_rule':           'INSERT INTO rules (title, slug) VALUES (%s, %s)',
            'insert_result':         'INSERT INTO results (value) VALUES (%s)',
            'fetch_rule_by_slug':    'SELECT id, title, slug FROM rules WHERE slug = %s',
            'fetch_scan_rules':      'SELECT RU.id, RU.slug, RU.title, RE.id, RE.value FROM rules AS RU \
                                      INNER JOIN rules_scans AS RS \
                                          ON RS.rule_id = RU.id \
                                      INNER JOIN scans AS S \
                                          ON RS.scan_id = S.id \
                                      INNER JOIN results AS RE \
                                          ON RS.result_id = RE.id \
                                      WHERE S.id = %s',
        }

        try:
            self.__conn = mysql.connector.connect(
                user     = args['user'],
                database = args['database'],
                password = args['password']
            )
        except mysql.connector.Error as err:
            self.__conn = None

            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.__error = "Something is wrong with your user name or password"
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.__error = "Database does not exist"
            else:
                self.__error = str(err)
        else:
            self.__cursor = self.__conn.cursor()

    def error(self):
        return self.__error

    def ready(self):
        return (self.__conn is not None)

    def saveScan(self, scan):
        if not self.ready():
            return

        scan = self.__saveScan(scan)

        for rule in scan.rules():
            stored_rule   = self.__fetchRule(rule.slug())
            stored_result = self.__fetchResultByValue(rule.result())

            if stored_result is None:
                stored_result = self.__saveResult(rule.result())

            if stored_rule is None:
                self.__saveRule(rule)
                stored_rule = rule

            self.__cursor.execute(
                self.__mysql_templates['insert_rule_result'],
                (scan.id(), stored_rule.id(), stored_result.id())
            )

        self.__commitToDB()

    def getAllScans(self):
        scans = []

        if not self.ready():
            return scans

        self.__cursor.execute(self.__mysql_templates['select_all_scans'])

        raw_scans = self.__cursor.fetchall()

        for id, slug in raw_scans:
            scan = Scan({
                'id': id,
                'slug': slug
            })
            self.__getScanRules(scan)
            scans.append(scan)

        return scans

    def getScanBySlug(self, slug):
        scan = None

        if not self.ready():
            return scan

        self.__cursor.execute(
            self.__mysql_templates['fetch_scan_by_slug'],
            (slug,)
        )

        res = self.__cursor.fetchall()
        if len(res) == 1:
            id, slug = res[0]
            scan = Scan({
                'id':   id,
                'slug': slug
            })
            self.__getScanRules(scan)

        return scan

    def __commitToDB(self):
        self.__conn.commit()

    def __saveScan(self, scan):
        scan_slug = datetime.now().strftime('%d.%m.%Y-%H:%M:%S')
        self.__cursor.execute(
            self.__mysql_templates['insert_scan'],
            (scan_slug,)
        )
        self.__commitToDB()

        stored_scan = Scan({
            'id':    self.__cursor.lastrowid,
            'slug':  scan_slug,
        })

        for rule in scan.rules():
            stored_scan.addTestedRule(rule)

        return stored_scan

    def __saveResult(self, result_value):
        self.__cursor.execute(
            self.__mysql_templates['insert_result'],
            (result_value,)
        )
        self.__commitToDB()

        return Result({
            'id':    self.__cursor.lastrowid,
            'value': result_value
        })

    def __fetchResultByValue(self, result_value):
        result = None
        self.__cursor.execute(
            self.__mysql_templates['fetch_result_by_value'],
            (result_value,)
        )
        res = self.__cursor.fetchall()
        if len(res) == 1:
            id, value = res[0]
            result = Result({
                'id':    id,
                'value': value,
            })

        return result

    def __saveRule(self, rule):
        self.__cursor.execute(
            self.__mysql_templates['insert_rule'],
            (rule.title(), rule.slug())
        )
        self.__commitToDB()
        rule.setId(self.__cursor.lastrowid)

    def __fetchRule(self, slug):
        rule = None
        self.__cursor.execute(
            self.__mysql_templates['fetch_rule_by_slug'],
            (slug,)
        )
        res = self.__cursor.fetchall()
        if len(res) == 1:
            id, title, slug = res[0]
            rule = Rule({
                'id':    id,
                'title': title,
                'slug':  slug
            })

        return rule

    def __getScanRules(self, scan):
        self.__cursor.execute(
            self.__mysql_templates['fetch_scan_rules'],
            (scan.id(),)
        )

        for rule_id, slug, title, result_id, value in self.__cursor:
            rule = Rule({
                'id':    rule_id,
                'slug':  slug,
                'title': title
            })
            result = Result({
                'id':    result_id,
                'value': value,
            })
            scan.addTestedRule(TestedRule(rule, result))

    def __del__(self):
        if self.__conn is not None:
            self.__conn.close()
