#!/usr/bin/env bash
# Install science-wiki-kit: link the skills into your agent's skills folder and, optionally, scaffold a wiki.
#
#   ./install.sh                 # link skills only
#   ./install.sh ~/my-wiki       # also scaffold a wiki (config, schema, templates, folders) in ~/my-wiki
#
# Environment: CLAUDE_SKILLS_DIR overrides the skills folder (default: ~/.claude/skills).
# Never overwrites a real directory or an existing config; existing files are skipped with a notice.
set -euo pipefail

KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-}"
SKILLS_DIR="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

command -v python3 >/dev/null 2>&1 || { echo "python3 (3.10 or newer) is required" >&2; exit 1; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' || { echo "Python 3.10 or newer is required" >&2; exit 1; }

echo "1/3 Python package (optional: skills also work through symlinks into this checkout)"
if python3 -m pip install --quiet --user -e "$KIT" 2>/dev/null; then
  echo "    installed wikikit in editable mode"
else
  echo "    pip install skipped (externally managed or unavailable); the skills still find wikikit through the symlinks"
fi

echo "2/3 Skills -> $SKILLS_DIR"
mkdir -p "$SKILLS_DIR"
for d in "$KIT"/skills/*/; do
  name="$(basename "$d")"
  dest="$SKILLS_DIR/$name"
  if [ -L "$dest" ]; then
    ln -sfn "${d%/}" "$dest"; echo "    relinked $name"
  elif [ -e "$dest" ]; then
    echo "    SKIPPED $name: $dest exists and is not a link (move it aside to install)"
  else
    ln -s "${d%/}" "$dest"; echo "    linked   $name"
  fi
done

echo "3/3 Wiki scaffold"
if [ -z "$TARGET" ]; then
  echo "    skipped (pass a folder to scaffold a wiki: ./install.sh ~/my-wiki)"
else
  mkdir -p "$TARGET/wiki"/{papers,concepts,methods,books,fields,debates} "$TARGET/templates"
  if [ ! -e "$TARGET/wiki.config.json" ]; then
    cp "$KIT/examples/minimal/wiki.config.json" "$TARGET/wiki.config.json"
    python3 "$KIT/tools/set_kit_dir.py" "$TARGET/wiki.config.json" "$KIT" >/dev/null
  fi
  [ -e "$TARGET/wiki/WIKI_SCHEMA.md" ] || cp "$KIT/docs/WIKI_SCHEMA.md" "$TARGET/wiki/WIKI_SCHEMA.md"
  for t in "$KIT"/templates/*.md; do
    [ -e "$TARGET/templates/$(basename "$t")" ] || cp "$t" "$TARGET/templates/"
  done
  [ -e "$TARGET/wiki/index.md" ] || printf '# Index\n' > "$TARGET/wiki/index.md"
  [ -e "$TARGET/wiki/log.md" ] || printf '# Log\n' > "$TARGET/wiki/log.md"
  [ -e "$TARGET/wiki/fields/MOC_Wiki.md" ] || printf -- '---\ntags: [MOC, hub]\ndate: %s\nstatus: active\ntype: MOC\n---\n\n# Hub\n\nThe top of the map. Link every field MOC here when you create it.\n\n## Fields\n' "$(date +%F)" > "$TARGET/wiki/fields/MOC_Wiki.md"
  echo "    scaffolded $TARGET (edit wiki.config.json and the Taxonomy section of wiki/WIKI_SCHEMA.md)"
fi

echo "Done. Next: cd to your wiki folder and run: python3 $KIT/skills/wiki-lint/scripts/lint.py"
