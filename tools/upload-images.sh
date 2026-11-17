#!/bin/bash
# Upload the images referenced by the blog (images-manifest.txt) to Cloudflare R2.
# Uses only macOS's built-in curl (SigV4 signing). Safe to re-run: files already in
# the bucket are skipped. Failures are listed in upload-failed.txt.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
IMG_DIR="$HOME/Documents/qqZone2026/QQ空间备份_36110494/Blogs/images"
MANIFEST="$HERE/images-manifest.txt"
FAILED="$HERE/upload-failed.txt"
PARALLEL=8

# Credentials live outside the git repo (qqblog-site/r2.env) so they are never pushed.
R2_ENV="${R2_ENV:-$HERE/../../r2.env}"
[ -f "$R2_ENV" ] || { echo "Missing $R2_ENV — see tools/README.md"; exit 1; }
set -a; source "$R2_ENV"; set +a
for v in R2_ACCOUNT_ID R2_ACCESS_KEY_ID R2_SECRET_ACCESS_KEY R2_BUCKET; do
  [ -n "${!v}" ] || { echo "r2.env: $v is empty"; exit 1; }
done
export R2_ENDPOINT="https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com/${R2_BUCKET}"
export IMG_DIR

upload_one() {
  f="$1"
  src="$IMG_DIR/$f"
  [ -f "$src" ] || { echo "MISSING-LOCAL $f"; return; }
  auth=(--aws-sigv4 "aws:amz:auto:s3" --user "$R2_ACCESS_KEY_ID:$R2_SECRET_ACCESS_KEY")
  code=$(curl -s -o /dev/null -w '%{http_code}' -I "${auth[@]}" "$R2_ENDPOINT/$f")
  [ "$code" = "200" ] && { echo "SKIP $f"; return; }
  type=$(file -b --mime-type "$src")
  for try in 1 2 3; do
    code=$(curl -s -o /dev/null -w '%{http_code}' -X PUT "${auth[@]}" \
      -H "Content-Type: $type" -H "Cache-Control: public, max-age=31536000" \
      --data-binary @"$src" "$R2_ENDPOINT/$f")
    [ "$code" = "200" ] && { echo "OK $f"; return; }
    sleep 2
  done
  echo "FAIL $f ($code)"
}
export -f upload_one

total=$(grep -c . "$MANIFEST")
echo "Uploading up to $total files to bucket $R2_BUCKET ..."
grep . "$MANIFEST" | xargs -P "$PARALLEL" -I{} bash -c 'upload_one "$1"' _ {} \
  | tee "$HERE/upload-log.txt" | awk -v t="$total" '{n++; c[$1]++} n%200==0 {printf "%d/%d done\n", n, t} END {for (k in c) print k, c[k]}'
grep -E '^(FAIL|MISSING-LOCAL)' "$HERE/upload-log.txt" > "$FAILED"
echo "Problems listed in $FAILED: $(wc -l < "$FAILED" | tr -d ' ')"
