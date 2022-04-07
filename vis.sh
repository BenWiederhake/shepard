#!/bin/sh

mpv --loop --lavfi-complex="[aid1]asplit[ao][a]; [a]showcqt[vo]" "$@"
