"""JSON, Markdown and self-contained HTML output."""

from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any

from .models import DiagnosticReport
from .privacy import sanitize_data


def _data(report: DiagnosticReport, sanitize: bool) -> dict[str, Any]:
    raw = report.to_dict()
    return sanitize_data(raw) if sanitize else raw


def render_json(report: DiagnosticReport, *, sanitize: bool = True) -> str:
    return json.dumps(_data(report, sanitize), indent=2, sort_keys=False) + "\n"


def render_markdown(report: DiagnosticReport, *, sanitize: bool = True) -> str:
    data = _data(report, sanitize)
    lines = [
        "# OpsProbe diagnostic report",
        "",
        f"- Generated: `{data['generated_at']}`",
        f"- Overall status: **{str(data['overall_status']).upper()}**",
        f"- Target: `{data['target'] or 'offline profile'}`",
        "",
        "## System context",
        "",
    ]
    for key, value in data["system"].items():
        lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")

    lines.extend(["", "## Checks", ""])
    for check in data["checks"]:
        lines.extend(
            [
                f"### {str(check['status']).upper()} — {check['name']}",
                "",
                check["summary"],
                "",
                f"Duration: `{check['duration_ms']} ms`",
            ]
        )
        if check.get("suggestion"):
            lines.extend(["", f"Next step: {check['suggestion']}"])
        lines.append("")

    lines.extend(["## Privacy note", "", data["privacy"]["sharing_note"], ""])
    return "\n".join(lines)


def render_html(report: DiagnosticReport, *, sanitize: bool = True) -> str:
    data = _data(report, sanitize)
    status = escape(str(data["overall_status"]))

    system_rows = "".join(
        f"<div><dt>{escape(key.replace('_', ' ').title())}</dt>"
        f"<dd>{escape(str(value))}</dd></div>"
        for key, value in data["system"].items()
    )

    cards: list[str] = []
    for check in data["checks"]:
        detail_rows = "".join(
            f"<tr><th>{escape(key.replace('_', ' ').title())}</th>"
            f"<td>{escape(str(value))}</td></tr>"
            for key, value in check["details"].items()
        )
        suggestion = (
            f'<p class="suggestion"><strong>Next:</strong> {escape(check["suggestion"])}</p>'
            if check.get("suggestion")
            else ""
        )
        check_status = escape(str(check["status"]))
        cards.append(
            f"""
            <article class="check-card {check_status}">
              <div class="check-heading">
                <span class="status-dot" aria-hidden="true"></span>
                <div><p class="eyebrow">{check_status}</p><h3>{escape(check['name'])}</h3></div>
                <span class="duration">{escape(str(check['duration_ms']))} ms</span>
              </div>
              <p>{escape(check['summary'])}</p>
              <table><tbody>{detail_rows}</tbody></table>
              {suggestion}
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>OpsProbe diagnostic report</title>
  <style>
    :root {{ color-scheme: dark; --bg:#08111f; --panel:#111e2f; --line:#26384f;
      --text:#eaf2ff; --muted:#91a4bd; --pass:#55d6a3; --warn:#ffcb66; --fail:#ff7185;
      --info:#75b9ff; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:radial-gradient(circle at 85% 0%,#14345a 0,transparent 34%),var(--bg);
      color:var(--text); font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,sans-serif; }}
    main {{ width:min(100% - 32px,980px); margin:0 auto; padding:64px 0; }}
    header {{ display:grid; grid-template-columns:1fr auto; gap:24px; align-items:end; margin-bottom:32px; }}
    h1,h2,h3,p {{ margin-top:0; }} h1 {{ font-size:clamp(2.2rem,7vw,4.8rem); line-height:.95;
      letter-spacing:-.06em; margin-bottom:16px; }} h2 {{ margin:34px 0 14px; font-size:1.1rem; }}
    h3 {{ margin:0; font-size:1.05rem; }} .lede,.meta,.duration,dd {{ color:var(--muted); }}
    .badge {{ border:1px solid var(--line); background:#0d1928; padding:10px 14px; border-radius:999px;
      text-transform:uppercase; font-size:.75rem; letter-spacing:.12em; }}
    .badge.pass {{ color:var(--pass); }} .badge.warn {{ color:var(--warn); }} .badge.fail {{ color:var(--fail); }}
    .system-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:10px; }}
    .system-grid div,.check-card {{ background:color-mix(in srgb,var(--panel) 88%,transparent); border:1px solid var(--line);
      border-radius:14px; box-shadow:0 20px 60px rgba(0,0,0,.16); }}
    .system-grid div {{ padding:14px 16px; }} dt,.eyebrow {{ color:var(--muted); font-size:.68rem;
      letter-spacing:.12em; text-transform:uppercase; }} dd {{ margin:3px 0 0; }}
    .checks {{ display:grid; gap:12px; }} .check-card {{ padding:18px; }} .check-heading {{ display:grid;
      grid-template-columns:auto 1fr auto; gap:12px; align-items:center; }}
    .status-dot {{ width:10px; height:10px; border-radius:50%; background:var(--info); box-shadow:0 0 16px currentColor; }}
    .pass .status-dot {{ background:var(--pass); }} .warn .status-dot {{ background:var(--warn); }}
    .fail .status-dot {{ background:var(--fail); }} .eyebrow {{ margin:0; }}
    table {{ width:100%; border-collapse:collapse; margin-top:12px; }} th,td {{ border-top:1px solid var(--line);
      padding:8px 0; text-align:left; }} th {{ width:42%; color:var(--muted); font-weight:500; }}
    .suggestion {{ margin:12px 0 0; padding:10px 12px; border-left:3px solid var(--info); background:#0b1726; }}
    footer {{ margin-top:30px; color:var(--muted); font-size:.8rem; }}
    @media(max-width:600px) {{ header {{ grid-template-columns:1fr; }} main {{ padding:34px 0; }} }}
  </style>
</head>
<body>
  <main>
    <header>
      <div><p class="meta">OPS / DIAGNOSTIC REPORT</p><h1>OpsProbe</h1>
        <p class="lede">Generated {escape(str(data['generated_at']))} · Target: {escape(str(data['target'] or 'offline profile'))}</p></div>
      <span class="badge {status}">{status}</span>
    </header>
    <section><h2>System context</h2><dl class="system-grid">{system_rows}</dl></section>
    <section><h2>Checks</h2><div class="checks">{''.join(cards)}</div></section>
    <footer>{escape(str(data['privacy']['sharing_note']))} · OpsProbe {escape(str(data['opsprobe_version']))}</footer>
  </main>
</body>
</html>
"""


def write_report(path: str | Path, content: str) -> Path:
    destination = Path(path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination
