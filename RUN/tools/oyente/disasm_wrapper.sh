#!/bin/bash
# disasm reads bytecode from stdin; strip swarm hash before passing through
sed -E 's/a165627a7a72305820[0-9a-f]{64}0029[[:space:]]*$//' | /usr/bin/disasm.real "$@"
