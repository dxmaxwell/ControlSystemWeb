#!/bin/bash

DIRNAME=`dirname "$0"`

exec softIoc -m "SBLNAME=2026X" -d "$DIRNAME/softBeamline.db"
