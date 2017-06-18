#!/usr/bin/env bash

# From https://stackoverflow.com/questions/59895/getting-the-source-directory-of-a-bash-script-from-within
# Get the actual directory of this script
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
   # resolve $SOURCE until the file is no longer a symlink
   DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
   SOURCE="$(readlink "$SOURCE")"
   # if $SOURCE was a relative symlink, we need to resolve it relative to
   # the path where the symlink file was located.
   [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

source $DIR/env/bin/activate && $DIR/gmail-filters $@
