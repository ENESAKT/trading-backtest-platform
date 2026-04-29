"""Güvenli proje eylemleri.

Yalnızca izin verilen komutlar çalıştırılır. rm, sudo, git push gibi
tehlikeli komutlar reddedilir. Çıktılar MAX_OUTPUT karakter ile kesilir.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import shlex
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
MAX_OUTPUT = 4000
TIMEOUT_SECONDS = 60

# Substring match ile reddedilen pattern'lar (lowercase karşılaştırma)
_FORBIDDEN: list[str] = [
    "rm ",
    "sudo",
    "git push",
    "git reset",
    "git clean",
    "git add -a",
    "git add .",
    "git commit",
    "git merge",
    "git rebase",
    "docker prune",
    "docker rm",
    "docker rmi",
    "> /dev",
    "chmod",
    "chown",
    "pkill",
    "killall",
    "drop table",
    "delete from",
    "truncate",
    ".env",
    "os.environ",
    # Gizli env değişkeni adlarını içeren komutlar
    "telegram_bot_token",
    "telegram_chat_id",
    "anthropic_api_key",
    "bot_token",
    "printenv",
    "export ",
    "/proc/",
    "cat /etc/",
]


def is_safe(command: str) -> tuple[bool, str]:
    """Komutun güvenli olup olmadığını dön: (ok, reason)."""
    cmd_lower = command.lower()
    for pattern in _FORBIDDEN:
        if pattern in cmd_lower:
            return False, f"Yasak pattern: `{pattern}`"
    return True, ""


def project_python() -> str:
    """Projede kullanılacak Python yorumlayıcısını seç."""
    venv_python = ROOT / ".venv" / "bin" / "python"
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


async def run_safe(
    command: str,
    cwd: str | None = None,
    timeout: int = TIMEOUT_SECONDS,
) -> tuple[int, str]:
    """Güvenli komut çalıştır. Döner: (returncode, output)."""
    ok, reason = is_safe(command)
    if not ok:
        return -1, f"❌ Güvenlik reddi: {reason}"

    work_dir = Path(cwd) if cwd else ROOT
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(work_dir),
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return -2, f"❌ Zaman aşımı ({timeout}s)"
        output = stdout.decode("utf-8", errors="replace")
        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n… (kısaltıldı, {len(output)} karakter)"
        return proc.returncode or 0, output
    except Exception as exc:  # noqa: BLE001
        logger.warning("safe_actions.run_safe hata: %s", exc)
        return -3, f"❌ Çalıştırma hatası: {exc}"


async def git_status() -> str:
    _, out = await run_safe("git status --short --branch")
    return out.strip() or "(temiz)"


async def git_diff_stat() -> str:
    _, out = await run_safe("git diff HEAD --stat")
    return out.strip() or "(değişiklik yok)"


async def git_log(n: int = 5) -> str:
    _, out = await run_safe(f"git log --oneline -{n}")
    return out.strip() or ""


async def run_pytest(path: str = "tests/", quick: bool = True) -> tuple[int, str]:
    flags = "-q --tb=short -x --timeout=30" if quick else "-q --tb=short"
    py = shlex.quote(project_python())
    return await run_safe(f"{py} -m pytest {shlex.quote(path)} {flags}", timeout=120)


async def run_tsc() -> tuple[int, str]:
    return await run_safe(
        "npx tsc --noEmit",
        cwd=str(ROOT / "piyasapilot-v2"),
        timeout=60,
    )


async def import_check() -> tuple[int, str]:
    """Kritik import'ları geçici script dosyasıyla test et."""
    import tempfile

    script = "\n".join([
        "from backend.api.main import create_app",
        "from backend.notifier.telegram import send_telegram",
        "from backend.notifier.main import get_notifier_status",
        "from backend.notifier.telegram_commands import COMMANDS",
        "from backend.notifier.telegram_listener import listener_loop",
        "from backend.paper.executor import PaperExecutor",
        "from backend.assistant.safe_actions import is_safe",
        "print('tum importlar OK - komut sayisi:', len(COMMANDS))",
    ])
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", dir=str(ROOT), delete=False
    )
    try:
        tmp.write(script)
        tmp.close()
        py = shlex.quote(project_python())
        code, out = await run_safe(f"{py} {shlex.quote(tmp.name)}", timeout=30)
    finally:
        import os as _os
        try:
            _os.unlink(tmp.name)
        except Exception:  # noqa: BLE001
            pass
    return code, out


async def grep_in_project(pattern: str, path: str = "backend/") -> str:
    safe_pattern = shlex.quote(pattern)
    _, out = await run_safe(
        f"grep -rn --include='*.py' {safe_pattern} {shlex.quote(path)}",
        timeout=10,
    )
    return out.strip() or "(bulunamadı)"


async def find_files(name_pattern: str, base: str = ".") -> str:
    safe_name = shlex.quote(f"*{name_pattern}*")
    _, out = await run_safe(
        f"find {shlex.quote(base)} -name {safe_name} "
        f"-not -path '*/node_modules/*' -not -path '*/__pycache__/*' "
        f"-not -path '*/.git/*'",
        timeout=10,
    )
    return out.strip() or "(bulunamadı)"
