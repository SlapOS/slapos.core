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
args = parser.parse_args()


# Extract slapos.core path and all dependencies from first promise found
# to import slapos.core

promise_folder = args.promise_folder
promise_file = next(
  p for p in os.listdir(promise_folder)
  if p.endswith('.py') and not p.startswith('__init__')
)
with open(os.path.join(promise_folder, promise_file)) as f:
  promise_content = f.read()
tree = ast.parse(promise_content, mode='exec')
assign_node = next(e for e in tree.body if isinstance(e, ast.Assign))
if sys.version_info >= (3, 9):
  assert ast.unparse(assign_node.targets[0]) == 'sys.path[0:0]'
else:
  assert [ast.dump(n) for n in assign_node.targets] \
      == [ast.dump(n) for n in ast.parse("sys.path[0:0] = []").body[0].targets]
sys.path[0:0] = ast.literal_eval(assign_node.value)

from slapos.grid.promise import PromiseLauncher, PromiseError
from slapos.cli.entry import SlapOSApp


# Configure promise launcher
# with the same logger as standard slapos command

app = SlapOSApp()
app.options, _ = app.parser.parse_known_args([])
app.configure_logging()

config = {k.replace('_', '-') : v for k, v in vars(args).items()}
promise_checker = PromiseLauncher(config=config, logger=app.log)


# Run promises
# Redirect stderr to stdout (logger uses stderr)
# to reserve stderr exclusively for error reporting

err = os.dup(2)
os.dup2(1, 2)

try:
  promise_checker.run()
except Exception as e:
  if sys.version_info < (3,):
    error_str = unicode(str(e), 'utf-8', 'repr')
  else:
    error_str = str(e)
  os.write(err, error_str.encode('utf-8', 'repr'))
  sys.exit(2 if isinstance(e, PromiseError) else 1)
