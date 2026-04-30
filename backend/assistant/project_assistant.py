"""Proje asistanı — Telegram görevlerini analiz eder, rapor üretir.

Asla otomatik commit/push yapmaz. Güvenli eylemler listesinden çıkar.
"""

from __future__ import annotations

import logging
from pathlib import Path

from backend.assistant.safe_actions import (
    git_diff_stat,
    git_log,
    git_status,
    grep_in_project,
    import_check,
    run_pytest,
    run_tsc,
)
from backend.config import getenv

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]


async def _health() -> dict:
    try:
        import httpx

        api_url = getenv("NOTIFY_API_URL", "http://localhost:8000")
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{api_url}/api/health")
            return r.json()
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}


async def project_health_report() -> str:
    """Tam proje sağlık kontrolü — /kontrol komutu."""
    lines: list[str] = ["🔍 *Proje Sağlık Kontrolü*\n"]

    # Git durumu
    lines.append("*Git:*")
    gs = await git_status()
    lines.append(f"```\n{gs[:600]}\n```")

    # Import testi — son anlamlı satırı al (DEBUG logları filtrele)
    lines.append("\n*Import testi:*")
    code, out = await import_check()
    icon = "✅" if code == 0 else "❌"
    last_line = next(
        (line for line in reversed(out.strip().splitlines()) if line.strip()),
        out.strip()[:100],
    )
    lines.append(f"{icon} `{last_line[:150]}`")

    # TypeScript
    lines.append("\n*TypeScript:*")
    tsc_code, tsc_out = await run_tsc()
    if tsc_code == 0:
        lines.append("✅ Temiz — sıfır hata")
    else:
        hata_satirlari = [line for line in tsc_out.splitlines() if "error" in line.lower()][:8]
        ozet = "\n".join(hata_satirlari) if hata_satirlari else tsc_out[:400]
        lines.append(f"❌ ```\n{ozet}\n```")

    # Pytest
    lines.append("\n*Testler (hızlı):*")
    py_code, py_out = await run_pytest(quick=True)
    if py_code == 0:
        summary_lines = [
            line for line in py_out.splitlines() if "passed" in line or "failed" in line
        ]
        lines.append(f"✅ {summary_lines[-1] if summary_lines else 'geçti'}")
    else:
        kisa = "\n".join(py_out.strip().splitlines()[-12:])
        lines.append(f"❌ ```\n{kisa}\n```")

    # Backend
    lines.append("\n*Backend (/api/health):*")
    health = await _health()
    if health.get("status") == "ok":
        version = health.get("version", "?")
        workers = health.get("workers", {})
        n_workers = len(workers) if isinstance(workers, (dict, list)) else 0
        lines.append(f"✅ Çalışıyor · v{version} · {n_workers} worker")
    else:
        lines.append(f"⚠️ {health.get('detail', 'Ulaşılamadı')}")

    lines.append("\n⚠️ Commit atılmadı.")
    return "\n".join(lines)


async def analyze_task(task_text: str) -> str:
    """/gorev komutu: analiz et, rapor ver, değişiklik yapma."""
    lines: list[str] = [
        "🔎 *GÖREV ANALİZİ*",
        f"📋 İstek: _{task_text[:120]}_\n",
    ]

    # Git durumu
    gs = await git_status()
    lines.append(f"*Git:*\n```\n{gs[:400]}\n```\n")

    # Anahtar kelimelerle dosya/kod ara
    keywords = [w for w in task_text.split() if len(w) > 3][:4]
    if keywords:
        lines.append("*İlgili kod:*")
        found_any = False
        for kw in keywords:
            found = await grep_in_project(kw)
            if found and found != "(bulunamadı)":
                short = "\n".join(found.splitlines()[:6])
                lines.append(f"`{kw}:`\n```\n{short}\n```")
                found_any = True
        if not found_any:
            lines.append("_(İlgili kod parçası bulunamadı)_")

    # Son commit geçmişi
    log = await git_log(3)
    if log:
        lines.append(f"\n*Son commitler:*\n```\n{log}\n```")

    lines.extend([
        "\n*Sonuç:* Analiz tamamlandı.",
        "Düzeltme için `/duzelt " + task_text[:60] + "` kullanın.",
        "\n⚠️ Commit atılmadı, dosya değiştirilmedi.",
    ])
    return "\n".join(lines)


async def fix_task(task_text: str) -> str:
    """/duzelt komutu: tanı koy, güvenli düzeltme uygula, rapor ver."""
    lines: list[str] = [
        "🔧 *DÜZELTME RAPORU*",
        f"📋 İstek: _{task_text[:120]}_\n",
    ]

    # Tanı
    imp_code, imp_out = await import_check()
    tsc_code, tsc_out = await run_tsc()
    diff_stat = await git_diff_stat()

    sorunlar: list[str] = []
    if imp_code != 0:
        sorunlar.append(f"Import hatası: {imp_out.strip()[:200]}")
    if tsc_code != 0:
        hata_satirlari = [line for line in tsc_out.splitlines() if "error" in line.lower()][:5]
        if hata_satirlari:
            sorunlar.append("TSC: " + " | ".join(hata_satirlari[:3]))

    # İlgili dosyaları bul
    keywords = [w for w in task_text.split() if len(w) > 4][:3]
    ilgili_dosyalar: list[str] = []
    for kw in keywords:
        found = await grep_in_project(kw)
        if found and found != "(bulunamadı)":
            dosyalar = [line.split(":")[0] for line in found.splitlines()[:4]]
            ilgili_dosyalar.extend(dosyalar)
    ilgili_dosyalar = list(dict.fromkeys(ilgili_dosyalar))[:6]

    # Sonuçları formatla
    lines.append("*Tespit edilen sorunlar:*")
    if sorunlar:
        for s in sorunlar:
            lines.append(f"• {s}")
    else:
        lines.append("• Import ve TSC temiz ✅")

    if ilgili_dosyalar:
        lines.append("\n*İlgili dosyalar:*")
        for f in ilgili_dosyalar:
            lines.append(f"  • `{f}`")

    lines.append(f"\n*Git farkı:*\n```\n{diff_stat[:400] or '(yok)'}\n```")

    # Test sonucu
    py_code, py_out = await run_pytest(quick=True)
    summary = [line for line in py_out.splitlines() if "passed" in line or "failed" in line]
    test_str = summary[-1] if summary else py_out.strip()[-80:]
    test_icon = "✅" if py_code == 0 else "❌"
    lines.append(f"\n*Test:* {test_icon} `{test_str}`")

    lines.extend([
        "\n*GÖREV RAPORU:*",
        f"• İstek: {task_text[:80]}",
        f"• Bulunan sorun: {sorunlar[0] if sorunlar else 'Tespit edilemedi'}",
        "• Yapılan düzeltme: Otomatik düzeltme uygulanmadı — manuel inceleme gerekli",
        f"• Değişen dosyalar: {', '.join(ilgili_dosyalar[:3]) if ilgili_dosyalar else 'Yok'}",
        f"• Test sonucu: {test_str}",
        "• Risk: Düşük — sadece analiz yapıldı",
        "• Commit önerisi: Sorun tespit edilip çözüldükten sonra commit at",
        "• Commit'e alınmaması: `.env`, `data/cache/`, `*.sqlite3`",
        "\n⚠️ Otomatik commit/push yapılmadı.",
    ])
    return "\n".join(lines)


async def assistant_status() -> dict:
    """API endpoint için asistan durum nesnesi."""
    return {
        "aktif": True,
        "listener": "long_polling",
        "llm": "claude-haiku (ANTHROPIC_API_KEY ile etkin)",
        "komutlar": [
            "/yardim", "/durum", "/fiyat", "/sinyal", "/strateji",
            "/ozet", "/son", "/hata", "/kontrol", "/gorev", "/duzelt",
        ],
    }
