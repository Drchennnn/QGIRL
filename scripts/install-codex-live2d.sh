#!/bin/bash
# 为 Live2D 项目安装 Codex 配置入口。
#
# Codex CLI 0.164.0 只读取 $CODEX_HOME/config.toml、$CODEX_HOME/<profile>.config.toml
# 和 $CODEX_HOME/agents/*.toml；项目内的 .codex/config.toml 不会加载。
# 因此这里用符号链接把项目内的配置源文件接到 Codex 的读取位置。
# 不会修改 CC Switch 管理的 config.toml、auth.json 或 model_providers。

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

if ! command -v codex >/dev/null 2>&1; then
  echo "找不到 codex 命令；请先安装 Codex CLI。" >&2
  exit 1
fi

mkdir -p "$CODEX_HOME/agents"

link_file() {
  local src="$1"
  local dst="$2"

  if [ ! -f "$src" ]; then
    echo "缺少源文件：$src" >&2
    exit 1
  fi

  if [ -L "$dst" ]; then
    local current
    current="$(readlink "$dst")"
    if [ "$current" = "$src" ]; then
      echo "已存在：$dst"
      return
    fi
    echo "拒绝覆盖已存在的不同符号链接：$dst -> $current" >&2
    echo "如果确认它是旧路径，请先手动删除再重跑本脚本。" >&2
    exit 1
  fi

  if [ -e "$dst" ]; then
    echo "拒绝覆盖已存在的文件：$dst" >&2
    exit 1
  fi

  ln -s "$src" "$dst"
  echo "已创建：$dst -> $src"
}

remove_legacy_link() {
  local dst="$1"
  local expected="$2"

  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$expected" ]; then
    rm "$dst"
    echo "已移除旧链接：$dst"
  fi
}

# 上一版按线路拆成两个 Profile；现在主模型由 Codex 界面选择，合并为一个。
remove_legacy_link "$CODEX_HOME/live2d-official.config.toml" \
  "$ROOT/codex/profiles/live2d-official.config.toml"
remove_legacy_link "$CODEX_HOME/live2d-beefapi.config.toml" \
  "$ROOT/codex/profiles/live2d-beefapi.config.toml"

link_file "$ROOT/codex/profiles/live2d.config.toml" \
  "$CODEX_HOME/live2d.config.toml"
link_file "$ROOT/codex/agents/live2d-reviewer.toml" \
  "$CODEX_HOME/agents/live2d-reviewer.toml"

echo
echo "Codex: $(codex --version 2>/dev/null || echo unknown)"
echo "CODEX_HOME: $CODEX_HOME"
echo
echo "启动（先在 CC Switch 切到官方 Plus 或 BeefAPI）："
echo "  $ROOT/scripts/codex-live2d"
echo
echo "脚本会自动识别当前线路；主模型请在 Codex 界面用 /model 选择。"
