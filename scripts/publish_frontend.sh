#!/usr/bin/env bash
# Preserve the existing CLI; shared publication commits DB before projection.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source_file="$(realpath "${1:-output/youtube_live.json}")"
cd "$script_dir/.."
exec python -m scripts.publish_youtube "$source_file"
