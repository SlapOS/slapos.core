#!/bin/sh
set -e

# Update an old dump to current format. Useful to update tests date
# when increasing database version number.
# Note that because it's what test expects, $COMPUTER_ID must be set to
# `computer` for slapos/tests/test_slapproxy/database_dump_version_??.sql
# and `slaprunner` for slapos/tests/test_slapproxy/database_dump_version_current.sql

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 computer_id dump_before.sql dump_after.sql"
    exit 1;
fi

COMPUTER_ID=$1
DUMP_BEFORE=$2
DUMP_AFTER=$3
PORT=6123

echo "Using slapos $(which slapos) : $(slapos --version 2>&1)"

TMPD=$(mktemp -d)
if [ ! -e $TMPD ]; then
    >&2 echo "Failed to create temp directory"
    exit 1
fi

trap "exit 1" HUP INT PIPE QUIT TERM
trap 'rm -rf "$TMPD"' exit

cat <<EOF > ${TMPD}/slapos.cfg
[slapos]
computer_id = $COMPUTER_ID
[slapproxy]
host = 127.0.0.1
port = $PORT
database_uri = ${TMPD}/proxy.db
EOF


sqlite3 ${TMPD}/proxy.db < $DUMP_BEFORE

slapos proxy start --cfg ${TMPD}/slapos.cfg &

# If you are running tests locally and you want to refer to the slapos being tested,
# you can use the test python executable in this way:
# cd ../../..
# python -m slapos.cli.entry proxy start --cfg ${TMPD}/slapos.cfg &
# cd -

SLAPOS_PROXY_PID=$!

curl --silent --retry-connrefused --retry 3 http://127.0.0.1:${PORT}/getComputerInformation?computer_id=$COMPUTER_ID

sqlite3 ${TMPD}/proxy.db .dump > $DUMP_AFTER

kill $SLAPOS_PROXY_PID
wait
