# How to update tests after database version upgrade ?

You've just updated the version of the database in `slapos/proxy/schema.sql`,
and you need to update the tests. You're in the right place!

Let's call `XX` the current version number and `YY` the new version.
Let's call `UU` the version number before `XX`.


## Prerequisites

A SlapOS node in which command `slapos` uses version `XX` of the database.
- e.g. a Theia in which you're locally developping `slapos.core`

A Python virtual environment in which the `slapos.core` egg is installed
from the loca repository with your changes, including the version upgrade
to `YY`.

For example, beside the `slapos.core` repository

```
$ python3 -m venv pyenv
$ source pyenv/bin/activate
(pyenv) $ cd slapos.core
(pyenv) $ pip install -e .
(pyenv) $ deactivate
$
```

The command `pip install -e <path>` installs the egg from sources at `<path>`
in editable mode, so that any change the source code is immediately taken
into account.

This provides a `slapos` command that uses version `YY` of the database
(assuming `slapos/proxy/schema.sql` has been updated in the source code)
whenever the virtual environment is activated.


## In `test_slapproxy.py`

- In `_MigrationTestCase`, update `current_version` from `XX` to `YY`.

- Add a `TestMigrateVersionXXToLatest` test case (see the existing ones).
  - If tables were added in version `XX`, adjust the `initial_table_list`.


## In `test_slapproxy/`

Go to `test_slapproxy/` (assuming you are at the root of `slapos.core`):

```
$ cd slapos/tests/test_slapproxy
```

With the Python virtual environment deactivated, run:

```
$ ./generate_dump.sh computer database_dump_version_UU.sql database_dump_version_XX.sql
```

This will call `slapos proxy start` with the `slapos` that uses version `XX`,
load the `database_dump_version_UU.sql` and migrate it to version `XX`, and
then dump it into a new file `database_dump_version_XX.sql`.

Now activate the virtual environment and run:
```
(pyenv) $ ./generate_dump.sh slaprunner database_dump_version_current.sql database_dump_version_current.sql
```

This will call `slapos proxy start` with `slapos` from the virtual environment
which has version `YY`, load `database_dump_version_current.sql` which is in
version `XX`, migrate it to `YY`, and then dump it back overwriting the file.
