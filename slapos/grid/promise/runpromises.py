import argparse
import ast
import os
import sys


# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument('--promise-folder', required=True)
parser.add_argument('--legacy-promise-folder', default=None)
parser.add_argument('--promise-timeout', type=int, default=20)
parser.add_argument('--partition-folder', default=None)
parser.add_argument('--log-folder', default=None)
parser.add_argument('--force', type=int, default=0)
parser.add_argument('--check-anomaly', type=int, default=0)
parser.add_argument('--debug', type=int, default=0)
parser.add_argument('--master-url', default=None)
parser.add_argument('--partition-cert', default=None)
parser.add_argument('--partition-key', default=None)
parser.add_argument('--partition-id', default=None)
parser.add_argument('--computer-id', default=None)
parser.add_argument('--only', action='append', default=None)
args = parser.parse_args()


# Parse slapos.core paths from any promise

promise_folder = args.promise_folder
promise_file = next(p for p in os.listdir(promise_folder) if p.endswith('.py'))
with open(os.path.join(promise_folder, promise_file)) as f:
  promise_content = f.read()
tree = ast.parse(promise_content, mode='exec')
paths = eval(compile(ast.Expression(tree.body[1].value), '', 'eval'))


# Import slapos.core
sys.path[0:0] = paths

from slapos.grid.promise import PromiseLauncher
from slapos.cli.entry import SlapOSApp


# Get the same logger as standard slapos command

app = SlapOSApp()
app.options, _ = app.parser.parse_known_args([])
app.configure_logging()
logger = app.log


# Run promises

config = { k.replace('_', '-') : v for k, v in vars(args).items() }
for key in ('debug', 'check-anomaly', 'force'):
  config[key] = bool(config[key])
config['--run-only-promise-list'] = config.pop('only')

promise_checker = PromiseLauncher(config=config, logger=logger)
promise_checker.run()
