#!/bin/bash

rm -f *.bdo
rm -f *.log

# large statistic example which should converge to the same result
shieldhit --nstat=1000 --seedoffset=1 --silent . 1>/dev/null &
shieldhit --nstat=1000 --seedoffset=2 --silent . 1>/dev/null &
shieldhit --nstat=1000 --seedoffset=3 --silent . 1>/dev/null &

# small statistic example which should deviate from run to run
shieldhit --nstat=10 --seedoffset=11 --silent . 1>/dev/null &
shieldhit --nstat=10 --seedoffset=12 --silent . 1>/dev/null &
shieldhit --nstat=10 --seedoffset=13 --silent . 1>/dev/null &
shieldhit --nstat=10 --seedoffset=14 --silent . 1>/dev/null &

# wait for all runs to finish, then exit with the exit code of the last run
wait
