#!/usr/bin/env bash
# 把一个册次目录下的所有单元文件按文件名排序合并成整册文件
# 用法: ./merge.sh "生成稿/初中/语文/九年级上册"
# 输出: 该目录下 00-整册合并.md（文件已存在则覆盖）
# 说明: 合并版用于整册审阅或一次性录入；常规入库仍建议按单元分次粘贴。
set -euo pipefail

DIR="${1:-}"
if [ -z "$DIR" ] || [ ! -d "$DIR" ]; then
  echo "用法: $0 <册次目录>"
  exit 1
fi

OUT="$DIR/00-整册合并.md"
TMP=$(mktemp)

first=1
for f in $(ls "$DIR"/*.md | grep -v "00-整册合并" | sort); do
  [ "$first" -eq 1 ] || printf '\n\n' >> "$TMP"
  cat "$f" >> "$TMP"
  first=0
done

mv "$TMP" "$OUT"
echo "已合并 $(ls "$DIR"/*.md | grep -v "00-整册合并" | wc -l) 个文件 -> $OUT ($(wc -c < "$OUT") 字节)"
