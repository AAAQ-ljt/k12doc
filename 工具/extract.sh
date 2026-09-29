#!/usr/bin/env bash
# 教材原件文本提取统一入口（PDF / pptx / docx，支持目录批量），内部调用 extract.py。
# 用法:
#   ./extract.sh "<输入文件或目录...>" "<输出txt>"
#   ./extract.sh --filter <文件名子串> "<目录>" "<输出txt>"
# 示例:
#   ./extract.sh "doc/小学/数学/[人教版] 义务教育教科书·数学五年级下册.pdf" "提取缓存/小学-数学-五年级下册.txt"
#   ./extract.sh --filter 一年级 "doc/小学/信息科技" "提取缓存/小学-信息科技-一年级全一册.txt"
# 环境要求: Git Bash + Python 3.8+ 即可。pip 依赖（python-pptx/pypdf/python-docx）首次用到自动
# 安装（或 pip install -r 工具/requirements.txt 预装）；pdftotext 有则 PDF 提取自动首选。
# 提取损失与对策详见 AGENTS.md 第八节。
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if command -v python >/dev/null 2>&1; then
  PY=(python)
elif command -v py >/dev/null 2>&1; then
  PY=(py -3)
else
  echo "错误: 未找到 Python（需要 3.8+），请安装后重试，或让 AI 助手代为处理。" >&2
  exit 1
fi

exec "${PY[@]}" "$DIR/extract.py" "$@"
