#!/usr/bin/env python3
"""
dump_conversation.py — 导出 Claude Code / Droid 会话为 Markdown
用法: python dump_conversation.py [--session-id UUID] [--source claude|droid|auto] [--output PATH]
默认: auto 模式取两个平台中最新会话,输出到 bigmemory/冷区/会话记录/YYYY-MM-DD_HHMM.md
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ------------------------------------------------------------------ #
#  常量
# ------------------------------------------------------------------ #

PROJ_DIR = Path(__file__).resolve().parents[2]                # DQN10/
BJ_TZ = timezone(timedelta(hours=8))                         # UTC+8

# Claude Code: ~/.claude/projects/<project-hash>/<session>.jsonl
CLAUDE_PROJ = Path.home() / ".claude" / "projects"
CC_PROJ_HASH = "-" + str(PROJ_DIR).replace("/", "-").lstrip("-")
CC_SESS_DIR = CLAUDE_PROJ / CC_PROJ_HASH

# Factory/Droid: ~/.factory/sessions/<project-hash>/<session>.jsonl
FACTORY_SESS = Path.home() / ".factory" / "sessions"
DROID_PROJ_HASH = "-" + str(PROJ_DIR).replace("/", "-").lstrip("-")
DROID_SESS_DIR = FACTORY_SESS / DROID_PROJ_HASH

# JSONL 格式标识
FORMAT_CLAUDE = "claude"
FORMAT_DROID = "droid"


# ------------------------------------------------------------------ #
#  格式检测
# ------------------------------------------------------------------ #

def detect_format(jsonl_path: Path) -> str:
    """读取第一行,自动判断是 Claude Code 还是 Droid 格式。

    Claude Code: 第一行 type 为 "queue-operation" 或 "user",
                 消息行顶层 type 为 "user"/"assistant"。
    Droid:       第一行 type 为 "session_start",
                 消息行顶层 type 为 "message",role 在 message.role。
    """
    with open(jsonl_path) as f:
        first = json.loads(f.readline())
    if first.get("type") == "session_start":
        return FORMAT_DROID
    return FORMAT_CLAUDE


# ------------------------------------------------------------------ #
#  会话发现
# ------------------------------------------------------------------ #

def find_latest_session(sess_dir: Path) -> Path | None:
    """找到目录下最新的 .jsonl 文件(按修改时间)"""
    if not sess_dir.exists():
        return None
    jsonls = sorted(sess_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    return jsonls[0] if jsonls else None


def find_session_by_id(session_id: str, source: str) -> Path | None:
    """按 session_id 查找 JSONL 文件"""
    candidates = []
    if source in ("claude", "auto"):
        p = CC_SESS_DIR / f"{session_id}.jsonl"
        if p.exists():
            candidates.append(p)
    if source in ("droid", "auto"):
        p = DROID_SESS_DIR / f"{session_id}.jsonl"
        if p.exists():
            candidates.append(p)
    return candidates[0] if candidates else None


def pick_latest(source: str) -> Path:
    """根据 source 参数选最新会话文件"""
    candidates = []
    if source in ("claude", "auto"):
        p = find_latest_session(CC_SESS_DIR)
        if p:
            candidates.append(p)
    if source in ("droid", "auto"):
        p = find_latest_session(DROID_SESS_DIR)
        if p:
            candidates.append(p)

    if not candidates:
        sys.exit(f"[错误] 未找到任何会话 (source={source})")

    # auto 模式取修改时间最新的
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


# ------------------------------------------------------------------ #
#  Claude Code subagent 发现
# ------------------------------------------------------------------ #

def find_cc_subagent_files(session_id: str) -> list[Path]:
    """找到 Claude Code 会话的所有 subagent JSONL"""
    sub_dir = CC_SESS_DIR / session_id / "subagents"
    if not sub_dir.exists():
        return []
    return sorted(sub_dir.glob("*.jsonl"), key=os.path.getmtime)


# ------------------------------------------------------------------ #
#  时间戳解析
# ------------------------------------------------------------------ #

def parse_timestamp(ts_str: str) -> datetime | None:
    """ISO 时间戳 → 北京时间,失败返回 None"""
    if not ts_str:
        return None
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.astimezone(BJ_TZ)
    except Exception:
        return None


# ------------------------------------------------------------------ #
#  内容提取(通用)
# ------------------------------------------------------------------ #

def extract_text(content) -> str:
    """从 message.content 中提取纯文本(跳过 thinking/tool_use/tool_result)"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if block.get("type") == "text":
                parts.append(block["text"].strip())
        return "\n\n".join(parts)
    return ""


def extract_tool_calls(content) -> list[str]:
    """提取 tool_use 摘要(工具名 + 简短参数)"""
    if not isinstance(content, list):
        return []
    calls = []
    for block in content:
        if block.get("type") == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {})
            summary_parts = []
            for k, v in inp.items():
                v_str = str(v)[:80]
                if len(str(v)) > 80:
                    v_str += "..."
                summary_parts.append(f"{k}={v_str}")
            summary = ", ".join(summary_parts[:3])
            if len(summary_parts) > 3:
                summary += ", ..."
            calls.append(f"`{name}({summary})`")
    return calls


# ------------------------------------------------------------------ #
#  跳过判断(通用)
# ------------------------------------------------------------------ #

def should_skip_user_text(text: str) -> bool:
    """判断用户消息是否应跳过(系统注入的 meta 内容)"""
    if not text:
        return True
    prefixes = (
        "<system-reminder>",
        "<task-notification>",
        "<local-command",
    )
    return text.startswith(prefixes)


def clean_command_text(text: str) -> str:
    """提取 command 名称(如有)"""
    if "<command-name>" in text:
        m = re.search(r"<command-name>(.*?)</command-name>", text)
        if m:
            return f"/{m.group(1)}"
    return text


# ------------------------------------------------------------------ #
#  Droid 格式解析
# ------------------------------------------------------------------ #

def process_droid_jsonl(jsonl_path: Path, label: str = "主会话") -> list[str]:
    """解析 Factory/Droid 的 JSONL。

    格式特征:
    - session_start 行: type="session_start", 含 id/title/owner/cwd
    - 消息行: type="message", message.role="user"/"assistant"
    - todo 行: type="todo_state"(跳过)
    - 用户真实输入在 content 列表的最后一个 text block
    - system-reminder 在 content 列表的前面 text block
    """
    lines = [f"### {label}", ""]
    session_title = ""

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            msg_type = obj.get("type")

            # 提取会话标题
            if msg_type == "session_start":
                session_title = (
                    obj.get("sessionTitle") or obj.get("title") or ""
                )
                continue

            if msg_type != "message":
                continue

            msg = obj.get("message", {})
            role = msg.get("role", "")
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")
            dt = parse_timestamp(ts_str)
            time_label = dt.strftime("%H:%M") if dt else ""

            if role == "user":
                # content 是 list[block],真实用户输入是最后一个非 system 的 text block
                text = _extract_real_user_text_droid(content)
                if not text:
                    continue
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif role == "assistant":
                text = extract_text(content)
                tools = extract_tool_calls(content)
                if not text and not tools:
                    continue
                lines.append(f"**AI** [{time_label}]:")
                if text:
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines, session_title


def _extract_real_user_text_droid(content) -> str:
    """从 Droid 用户消息的 content blocks 中提取真实用户输入。

    Droid 的 user message content 通常为:
    [text(system-reminder), text(system-reminder), ..., text(真实输入)]
    或 [tool_result] (工具返回,跳过)
    """
    if isinstance(content, str):
        if should_skip_user_text(content):
            return ""
        return content.strip()

    if not isinstance(content, list):
        return ""

    # 从后往前找第一个不是 system-reminder 的 text block
    for block in reversed(content):
        if block.get("type") != "text":
            continue
        text = block.get("text", "").strip()
        if not should_skip_user_text(text):
            return text

    return ""


# ------------------------------------------------------------------ #
#  Claude Code 格式解析
# ------------------------------------------------------------------ #

def process_claude_jsonl(jsonl_path: Path, label: str = "主会话") -> list[str]:
    """解析 Claude Code 的 JSONL。

    格式特征:
    - 消息行顶层 type 为 "user"/"assistant"
    - isMeta=true 的 user 消息跳过
    - content 可以是 str 或 list[block]
    """
    lines = [f"### {label}", ""]

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            msg_type = obj.get("type")

            if msg_type not in ("user", "assistant"):
                continue

            msg = obj.get("message", {})
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")
            dt = parse_timestamp(ts_str)
            time_label = dt.strftime("%H:%M") if dt else ""

            if msg_type == "user":
                # 跳过 meta 消息
                if obj.get("isMeta"):
                    continue
                text = extract_text(content)
                if should_skip_user_text(text):
                    continue
                text = clean_command_text(text)
                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif msg_type == "assistant":
                text = extract_text(content)
                tools = extract_tool_calls(content)
                if not text and not tools:
                    continue
                lines.append(f"**AI** [{time_label}]:")
                if text:
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines, ""


# ------------------------------------------------------------------ #
#  统一入口
# ------------------------------------------------------------------ #

def process_jsonl(jsonl_path: Path, label: str = "主会话") -> tuple[list[str], str]:
    """自动检测格式并解析,返回 (markdown行列表, 会话标题)"""
    fmt = detect_format(jsonl_path)
    if fmt == FORMAT_DROID:
        return process_droid_jsonl(jsonl_path, label)
    return process_claude_jsonl(jsonl_path, label)


def detect_platform_label(jsonl_path: Path) -> str:
    """返回平台标签用于输出元数据"""
    fmt = detect_format(jsonl_path)
    if fmt == FORMAT_DROID:
        # 从 settings.json 读取模型信息
        settings_path = jsonl_path.with_suffix(".settings.json")
        model = "?"
        if settings_path.exists():
            try:
                with open(settings_path) as f:
                    s = json.load(f)
                model = s.get("model", "?")
            except Exception:
                pass
        return f"Droid ({model})"
    return "Claude Code"


# ------------------------------------------------------------------ #
#  主流程
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(
        description="导出 Claude Code / Droid 会话为 Markdown"
    )
    parser.add_argument("--session-id", help="指定会话 UUID,默认取最新")
    parser.add_argument(
        "--source", "-s",
        choices=["claude", "droid", "auto"],
        default="auto",
        help="选择平台: claude / droid / auto(默认 auto,取两边最新)",
    )
    parser.add_argument("--output", "-o", help="输出路径,默认 bigmemory/冷区/会话记录/")
    args = parser.parse_args()

    # ---- 定位会话文件 ---- #
    if args.session_id:
        jsonl_path = find_session_by_id(args.session_id, args.source)
        if not jsonl_path:
            sys.exit(f"[错误] 找不到会话: {args.session_id} (source={args.source})")
    else:
        jsonl_path = pick_latest(args.source)

    session_id = jsonl_path.stem
    mod_time = datetime.fromtimestamp(jsonl_path.stat().st_mtime, tz=BJ_TZ)
    platform = detect_platform_label(jsonl_path)
    fmt = detect_format(jsonl_path)

    print(f"[信息] 平台: {platform}")
    print(f"[信息] 会话: {session_id}")
    print(f"[信息] 文件: {jsonl_path}")
    print(f"[信息] 大小: {jsonl_path.stat().st_size / 1024:.0f} KB")

    # ---- 解析主会话 ---- #
    md_lines = []
    content_lines, session_title = process_jsonl(jsonl_path, "主会话")

    md_lines.append("# 会话记录")
    md_lines.append(f"> 会话 ID: `{session_id}`")
    md_lines.append(f"> 平台: {platform}")
    if session_title:
        md_lines.append(f"> 标题: {session_title}")
    md_lines.append(f"> 导出时间: {mod_time.strftime('%Y-%m-%d %H:%M')}")
    md_lines.append("")
    md_lines.extend(content_lines)

    # ---- 解析 subagent(仅 Claude Code 有子目录结构) ---- #
    if fmt == FORMAT_CLAUDE:
        sub_files = find_cc_subagent_files(session_id)
        if sub_files:
            md_lines.append("---")
            md_lines.append("")
            md_lines.append("## Subagent 会话")
            md_lines.append("")
            for sf in sub_files:
                agent_name = sf.stem
                sub_lines, _ = process_jsonl(sf, f"Agent: {agent_name}")
                md_lines.extend(sub_lines)
                md_lines.append("---")
                md_lines.append("")

    # ---- 输出 ---- #
    output_text = "\n".join(md_lines)

    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = PROJ_DIR / "bigmemory" / "冷区" / "会话记录"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{mod_time.strftime('%Y-%m-%d_%H%M')}.md"

    out_path.write_text(output_text, encoding="utf-8")
    print(f"[完成] 已导出到 {out_path}")
    print(f"[信息] 共 {len(output_text)} 字符, {output_text.count(chr(10))} 行")


if __name__ == "__main__":
    main()
