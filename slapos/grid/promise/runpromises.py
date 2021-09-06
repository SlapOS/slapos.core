from __future__ import print_function

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
parser.add_argument('--force', action='store_true')
parser.add_argument('--check-anomaly', action='store_true')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--master-url', default=None)
parser.add_argument('--partition-cert', default=None)
parser.add_argument('--partition-key', default=None)
parser.add_argument('--partition-id', default=None)
parser.add_argument('--computer-id', default=None)
parser.add_argument('--only', action='append', default=None)
args = parser.parse_args()


# Parse slapos.core paths from any promise

promise_folder = args.promise_folder
promise_file = next(
  p for p in os.listdir(promise_folder)
  if p.endswith('.py') and not p.startswith('__init__')
)
with open(os.path.join(promise_folder, promise_file)) as f:
  promise_content = f.read()
tree = ast.parse(promise_content, mode='exec')
paths = eval(compile(ast.Expression(tree.body[1].value), '', 'eval'))


# Import slapos.core

sys.path[0:0] = paths

from slapos.grid.promise import PromiseLauncher, PromiseError
from slapos.cli.entry import SlapOSApp


# Get the same logger as standard slapos command

app = SlapOSApp()
app.options, _ = app.parser.parse_known_args([])
app.configure_logging()
logger = app.log


# Run promises (the logger only uses stderr so stdout should be unused)

config = { k.replace('_', '-') : v for k, v in vars(args).items() }
config['run-only-promise-list'] = config.pop('only')

promise_checker = PromiseLauncher(config=config, logger=logger)
try:
  promise_checker.run()
except PromiseError as e:
  print(e)
  exit(2)
except Exception as e:
  print(e)
  exit(1)
