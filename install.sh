#!/usr/bin/env bash
# ChatMate — macOS installer
# Usage: curl -fsSL https://raw.githubusercontent.com/michaelabrowne/chatMate/develop/install.sh | bash
set -euo pipefail

REPO="michaelabrowne/chatMate"
INSTALL_DIR="/Applications"

echo "==> Fetching latest release..."
DOWNLOAD_URL=$(curl -fsL "https://api.github.com/repos/$REPO/releases/latest" \
  | grep '"browser_download_url"' \
  | grep 'mac\.dmg' \
  | cut -d'"' -f4)

if [[ -z "$DOWNLOAD_URL" ]]; then
  echo "Error: could not find a macOS release. Check https://github.com/$REPO/releases"
  exit 1
fi

echo "==> Downloading $(basename "$DOWNLOAD_URL")..."
TMP=$(mktemp -d)
DMG="$TMP/ChatMate.dmg"
# Redirect stdin from /dev/null — prevents curl consuming the bash script pipe
curl -L --progress-bar "$DOWNLOAD_URL" -o "$DMG" < /dev/null

echo "==> Mounting disk image..."
# -plist gives structured output; < /dev/null prevents hdiutil consuming the script pipe
MOUNT_POINT=$(hdiutil attach "$DMG" -nobrowse -plist < /dev/null 2>/dev/null | \
  python3 -c "
import sys, plistlib
data = plistlib.loads(sys.stdin.buffer.read())
mps = [e['mount-point'] for e in data.get('system-entities', []) if 'mount-point' in e]
print(mps[0] if mps else '')
")

if [[ -z "$MOUNT_POINT" ]]; then
  echo "Error: could not mount the disk image."
  rm -rf "$TMP"
  exit 1
fi

APP_BUNDLE=$(find "$MOUNT_POINT" -maxdepth 1 -name "*.app" -type d | head -1)
if [[ -z "$APP_BUNDLE" ]]; then
  echo "Error: no .app bundle found inside the DMG."
  hdiutil detach "$MOUNT_POINT" -quiet < /dev/null 2>/dev/null || true
  rm -rf "$TMP"
  exit 1
fi

APP_NAME=$(basename "$APP_BUNDLE")
echo "==> Installing $APP_NAME to $INSTALL_DIR..."
rm -rf "$INSTALL_DIR/$APP_NAME"
cp -R "$APP_BUNDLE" "$INSTALL_DIR/"

echo "==> Removing quarantine flag..."
xattr -cr "$INSTALL_DIR/$APP_NAME"

echo "==> Cleaning up..."
hdiutil detach "$MOUNT_POINT" -quiet < /dev/null 2>/dev/null
rm -rf "$TMP"

echo ""
echo "  $APP_NAME installed successfully."
echo "  Launching..."
open "$INSTALL_DIR/$APP_NAME"
