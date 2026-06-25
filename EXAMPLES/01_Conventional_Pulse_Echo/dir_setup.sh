#!/bin/bash
#
# script runs mesher and solver (in serial)
# using this example setup
#

set -e

echo "running example: $(date)"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPECFEM2D_DIR="${SPECFEM2D_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# sets up directory structure in current example directoy
echo
echo "setting up example..."
echo

cd "$SCRIPT_DIR"

mkdir -p OUTPUT_FILES


#Make DATA dir if not exist
mkdir -p DATA


# links executables
mkdir -p bin
cd bin/
if [ ! -d "$SPECFEM2D_DIR/bin" ]; then
  echo "ERROR: SPECFEM2D bin directory not found: $SPECFEM2D_DIR/bin"
  echo "Set SPECFEM2D_DIR=/path/to/specfem2d before running this script."
  exit 1
fi

for executable in "$SPECFEM2D_DIR"/bin/*; do
  [ -e "$executable" ] || continue
  link_target="$executable"
  if command -v realpath >/dev/null 2>&1; then
    link_target="$(realpath --relative-to="$PWD" "$executable" 2>/dev/null || printf '%s' "$executable")"
  fi
  ln -sf "$link_target" .
done
