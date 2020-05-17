#!/bin/bash

PIPE=/tmp/terminal

if [[ -p /tmp/terminal ]] ; then
    exit
fi

gnome-terminal -- bash -c 'mkfifo /tmp/terminal && trap "rm -f /tmp/terminal" EXIT ; while true ; do while read LINE ; do eval "${LINE}" ; done < /tmp/terminal ; done'
