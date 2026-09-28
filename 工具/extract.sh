#!/usr/bin/env bash
# 教材 PDF 文本提取（本机已验证：xpdf/poppler pdftotext 4.00）
# 用法: ./extract.sh "<pdf路径>" "<输出txt路径>"
# 示例: ./extract.sh "doc/小学/数学/[人教版] 义务教育教科书·数学五年级下册.pdf" "提取缓存/小学-数学-五年级下册.txt"
set -euo pipefail

PDF="${1:-}"
OUT="${2:-}"

if [ -z "$PDF" ] || [ -z "$OUT" ]; then
  echo "用法: $0 <pdf路径> <输出txt路径>"
  exit 1
fi
if [ ! -f "$PDF" ]; then
  echo "错误: 找不到 PDF 文件: $PDF"
  exit 1
fi

mkdir -p "$(dirname "$OUT")"
pdftotext -enc UTF-8 "$PDF" "$OUT"

BYTES=$(wc -c < "$OUT")
echo "已提取: $OUT (${BYTES} 字节)"
echo ""
echo "自查提醒:"
echo "1. 若上方出现 'Unknown character collection Adobe-GB1' / 'SimSun' 报错："
echo "   文本主体通常仍可提取，但部分宋体内容可能缺失，编改前必须通读全文，"
echo "   发现语义断裂按学科通识补全并标注（以本教材为准）；丢字严重时改用 pypdf/PDFBox 提取。"
echo "2. 若输出只有几 KB：可能是扫描版 PDF（无文字层），需 OCR，勿硬提。"
