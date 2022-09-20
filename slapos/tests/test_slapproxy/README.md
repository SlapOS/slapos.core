# How to update tests after database version upgrade ?

You've just updated the version of the database in `slapos/proxy/schema.sql`,
and you need to update the tests. You're in the right place!

Let's call `XX` the current version number and `YY` the new version.
Let's call `UU` the version number before `XX`.


## Prerequisites

- A SlapOS node in which command `slapos` uses version `XX` of the database.
  - e.g. a Theia in which you're locally developping `slapos.core`
  - alternatively, a full SlapOS Node should work as well

- A test environment for `slapos.core`:
  - install SR `slapos-testing`
  - source the environment so that `python` refers to one for the tests
  - from repository root: `python -m unittest -v slapos.tests.test_slapproxy`

A test environment for `slapos.core` is not strictly required, but you'll
probably want to run the tests locally anyway, and it's a convenient way
to provide all the dependencies for `slapos.core`.


## In `test_slapproxy.py`

- In `_MigrationTestCase`, update `current_version` from `XX` to `YY`.

- Add a `TestMigrateVersionXXToLatest` test case.
  - If tables were added in version `XX`, adjust the `initial_table_list`.


## In `test_slapproxy/`

From `test_slapproxy/`, run:

```
./generate_dump computer database_dump_version_UU.sql database_dump_version_XX.sql
```

This script will call `slapos proxy start` to start a proxy of version `XX`.

And:
```
PATH=$PWD/bin:$PATH ./generate_dump slaprunner database_dump_version_current.sql database_dump_version_current.sql
```

The `PATH=$PWD/bin:$PATH` bit places `./bin/slapos` in the path, which is a
`slapos` that refers the current code in this `slapos.core` repository, using
the `python` provided by `slapos-testing` to get all the needed dependencies.

So that way `slapos proxy start` will start a proxy of version `YY`.
