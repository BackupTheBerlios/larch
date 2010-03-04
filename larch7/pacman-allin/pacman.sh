#!/bin/bash

FULLPATH="$( readlink -f $0 )"
LIBDIR="$( dirname ${FULLPATH} )/lib"
$LIBDIR/loader --library-path $LIBDIR $LIBDIR/pacman $*
