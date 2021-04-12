import sys
import configparser
import argparse
from commands import COMMANDS
from scanmanager import ScanManager

epilog_str = "Use: %(prog)s [{}] {{-h|--help}} to see a commands help page".format('|'.join(COMMANDS.keys()))
parser     = argparse.ArgumentParser(epilog=epilog_str, description="Small wrapper on oscap command")
subparsers = parser.add_subparsers(title='commands', description='valid commands', dest="cmd_name")
for cmd in COMMANDS.keys():
    cmd_parser = subparsers.add_parser(cmd, description=COMMANDS[cmd].helpStr())
    COMMANDS[cmd].addArguments(cmd_parser)

args_dict = vars(parser.parse_args())

if args_dict['cmd_name'] is None:
    parser.print_help()
    exit(1)

config = configparser.ConfigParser()
config.read('config.ini')

db_user = None
db_name = None
db_pass = None

if 'database' in config:
    db_user = config['database'].get('user', None)
    db_name = config['database'].get('database', None)
    db_pass = config['database'].get('password', None)
else:
    print("No database credentials found")
    exit(1)

if None in (db_user, db_name, db_pass):
    print("Missing database credentials")
    exit(1)

smanager = ScanManager({
    'user':     db_user,
    'database': db_name,
    'password': db_pass
})
command = COMMANDS[args_dict['cmd_name']](smanager, args_dict)

excode = 0
if smanager.ready():
    excode = command.exec()
    print(command.output())

    for error in command.errors():
        print(error)
else:
    excode = 1
    print(smanager.error())

exit(excode)
