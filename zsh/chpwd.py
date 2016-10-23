import os
import sys
import json
import hashlib
import imp
import types
import warnings

warnings.filterwarnings("ignore")

try:
    import zsh
    eval = zsh.eval
except ImportError:
    def eval(command):
        print(command)


dirrc = sys.modules['dirrc'] = types.ModuleType('dirrc')


KNOWN_FILE_PATH = os.path.expanduser('~/.dirrc_known_files')


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

try:
    with open(KNOWN_FILE_PATH) as file:
        known_files = json.loads(file.read())
except:
    known_files = {}


def check_rc(rc_path, hash):
    key = '{}:{}'.format(rc_path, hash)
    if key not in known_files:
        known_files[key] = query_yes_no(
            'Do you want to run an unknown file({})?'.format(key)
        )
        with open(KNOWN_FILE_PATH, 'w+') as file:
            file.write(json.dumps(known_files))
    return known_files[key]


def init_rc(rc_path):
    if not check_rc(rc_path, filehash(rc_path)):
        return
    print('init-{}'.format(rc_path))
    rc = imp.load_source(rc_path, rc_path)
    if 'init' in dir(rc):
        rc.init()


def exit_rc(rc_path):
    if not check_rc(rc_path, filehash(rc_path)):
        return
    print('exit-{}'.format(rc_path))
    rc = imp.load_source(rc_path, rc_path)
    if 'exit' in dir(rc):
        rc.exit()


def setenv(name, value):
    if isinstance(name, str):
        name = json.dumps(name)
    else:
        raise Error
    if isinstance(value, str):
        value = json.dumps(value)
    elif value is None:
        pass
    else:
        raise Error
    if value is None:
        eval('unset {}'.format(name))
    else:
        eval('export {}={}'.format(name, value))


dirrc.setenv = setenv
dirrc.system = eval


def filehash(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()


# root 권한으로 실행하면 보안문제 발생할 가능성이 있음
if os.getuid() == 0 or os.geteuid == 0:
    exit()


# TODO: known file list를 로드

if len(sys.argv) < 2:
    path = os.getcwd()
else:
    path = os.path.abspath(sys.argv[1])

rcfiles = []
while path != '/':
    filepath = os.path.join(path, '.dirrc')
    if os.path.isfile(filepath):
        rcfiles.append([filepath, filehash(filepath)])
    path = os.path.abspath(os.path.join(path, os.pardir))
rcfiles.reverse()

current_rcfiles = json.loads(os.environ.get('DIRRC_LIST', '[]'))

while rcfiles[:len(current_rcfiles)] != current_rcfiles:
    path, hash = current_rcfiles[-1]
    exit_rc(path)
    current_rcfiles = current_rcfiles[:-1]

while rcfiles != current_rcfiles:
    path, hash = rcfiles[len(current_rcfiles)]
    init_rc(path)
    current_rcfiles.append([path, hash])

os.environ['DIRRC_LIST'] = json.dumps(current_rcfiles)
