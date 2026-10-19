#!/usr/bin/env python3
"""
Пересчитывает прогресс студенческих проектов.

Что делает:
  1. Читает data/projects.json (список студентов и их проектов).
  2. Создаёт папку projects/<Студент>/<N_проект>/ с TASK.md, если её ещё нет.
  3. Проект считается ЗАГРУЖЕННЫМ, если в его папке есть хоть один файл,
     кроме TASK.md / .gitkeep.
  4. По истории git находит, каким коммитом/PR проект загружен и когда.
  5. Перезаписывает README.md (с галками) и docs/progress.json (для сайта).

Запускается автоматически GitHub Action'ом после каждого push в main
(то есть после каждого принятого pull request). Можно запустить и руками:
    python scripts/update_progress.py
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "projects.json"
INTRO = ROOT / "data" / "README_intro.md"
README = ROOT / "README.md"
PROGRESS_JSON = ROOT / "docs" / "progress.json"

IGNORED_FILES = {"TASK.md", ".gitkeep", ".DS_Store", "Thumbs.db", "desktop.ini"}
MSK = timezone(timedelta(hours=3))


# ---------------------------------------------------------------- helpers
def git(*args):
    try:
        res = subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except FileNotFoundError:
        return ""


def gh_api(path):
    """Запрос к GitHub API (работает только внутри Action, где есть токен)."""
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/{path}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        print(f"  ! GitHub API {path}: {e}", file=sys.stderr)
        return None


def fmt_date(iso):
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(MSK)
        return dt.strftime("%d.%m.%Y")
    except ValueError:
        return iso[:10]


def bar(done, total, width=10):
    filled = round(width * done / total) if total else 0
    return "█" * filled + "░" * (width - filled)


def task_md(student, p, data):
    lines = [
        f"# {p['n']}. {p['title']}",
        "",
        f"**Участник:** {student['name']}",
        "",
        "> Положите сюда файлы проекта (код, отчёт `REPORT.md`/PDF, docker-compose, скриншоты)",
        "> и откройте Pull Request. После того как PR примут, проект автоматически",
        "> отметится галкой в README и на сайте.",
        "",
        "## Что нужно сделать",
        p["task"],
        "",
        "## Технологии",
        ", ".join(p["tech"]),
        "",
        "## Архитектура",
        p["architecture"],
        "",
        "## Паттерны",
        ", ".join(p["patterns"]),
        "",
        "## Что показать в отчёте",
    ]
    lines += [f"{i}. {item}" for i, item in enumerate(data["report_checklist"], 1)]
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- scan
def find_submission(rel_dir):
    """Ищет последний коммит в main, который принёс файлы в папку проекта."""
    spec = [rel_dir, f":(exclude){rel_dir}/TASK.md", f":(exclude){rel_dir}/.gitkeep"]
    line = git("log", "--first-parent", "-1", "--format=%H%x1f%cI%x1f%an%x1f%s", "--", *spec)
    if not line:
        return {}
    sha, date, author, subject = (line.split("\x1f") + ["", "", "", ""])[:4]
    info = {"sha": sha, "date": date, "author": author}

    # 1) точный способ — спросить GitHub, какому PR принадлежит коммит
    prs = gh_api(f"commits/{sha}/pulls") or []
    prs = [p for p in prs if p.get("merged_at")] or prs
    if prs:
        pr = prs[0]
        info.update(pr=pr["number"], pr_url=pr["html_url"], pr_title=pr.get("title", ""),
                    login=(pr.get("user") or {}).get("login", ""),
                    date=pr.get("merged_at") or date)
        return info

    # 2) запасной способ — разобрать сообщение коммита
    m = re.match(r"Merge pull request #(\d+) from ([^/\s]+)/", subject) or \
        re.search(r"\(#(\d+)\)\s*$", subject)
    if m:
        info["pr"] = int(m.group(1))
        if m.lastindex and m.lastindex >= 2:
            info["login"] = m.group(2)
    return info


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    repo = os.environ.get("GITHUB_REPOSITORY") or data["repo"]
    branch = data.get("branch", "main")
    pdir = data.get("projects_dir", "projects")
    owner, name = repo.split("/")
    site_url = f"https://{owner.lower()}.github.io/{name}/"
    repo_url = f"https://github.com/{repo}"

    out_students, total, done_total = [], 0, 0
    for s in data["students"]:
        sdir = ROOT / pdir / s["slug"]
        projects = []
        for p in s["projects"]:
            folder = sdir / p["slug"]
            folder.mkdir(parents=True, exist_ok=True)
            task = folder / "TASK.md"
            if not task.exists():
                task.write_text(task_md(s, p, data), encoding="utf-8", newline="\n")

            files = [f for f in folder.rglob("*")
                     if f.is_file() and f.name not in IGNORED_FILES and ".git" not in f.parts]
            done = bool(files)
            rel = f"{pdir}/{s['slug']}/{p['slug']}"
            sub = find_submission(rel) if done else {}
            if sub.get("pr") and not sub.get("pr_url"):
                sub["pr_url"] = f"{repo_url}/pull/{sub['pr']}"
            projects.append({
                **p,
                "path": rel,
                "url": f"{repo_url}/tree/{branch}/{rel}",
                "done": done,
                "files": len(files),
                "submitted_at": sub.get("date", ""),
                "pr": sub.get("pr"),
                "pr_url": sub.get("pr_url", ""),
                "by": sub.get("login") or sub.get("author", ""),
                "by_login": bool(sub.get("login")),
            })
            total += 1
            done_total += done
        out_students.append({
            "name": s["name"], "slug": s["slug"], "path": f"{pdir}/{s['slug']}",
            "done": sum(p["done"] for p in projects), "total": len(projects),
            "projects": projects,
        })

    now = datetime.now(MSK)
    progress = {
        "title": data["title"], "repo": repo, "repo_url": repo_url, "site_url": site_url,
        "updated_at": now.isoformat(timespec="seconds"),
        "done": done_total, "total": total,
        "report_checklist": data["report_checklist"],
        "report_template": data["report_template"],
        "students": out_students,
    }
    PROGRESS_JSON.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_JSON.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
    README.write_text(render_readme(progress, data, pdir), encoding="utf-8", newline="\n")
    print(f"Готово: загружено {done_total} из {total} проектов")


# ---------------------------------------------------------------- README
def render_readme(pr, data, pdir):
    pct = round(100 * pr["done"] / pr["total"]) if pr["total"] else 0
    badge = f"https://img.shields.io/badge/progress-{pr['done']}%2F{pr['total']}%20({pct}%25)-{'brightgreen' if pct == 100 else 'blue'}"
    L = [
        "<!-- Этот файл генерируется автоматически скриптом scripts/update_progress.py. -->",
        "<!-- Не редактируйте его руками: текст вступления меняется в data/README_intro.md -->",
        "",
        f"# {pr['title']}",
        "",
        f"[![progress]({badge})]({pr['site_url']}) ",
        "",
        f"🌐 **Сайт с проектами:** {pr['site_url']}  ",
        f"🕒 Обновлено: {datetime.fromisoformat(pr['updated_at']).strftime('%d.%m.%Y %H:%M')} (МСК)",
        "",
    ]
    if INTRO.exists():
        L += [INTRO.read_text(encoding="utf-8").strip(), ""]

    L += ["## Сводка", "", "| Участник | Сдано | Прогресс |", "|---|:---:|---|"]
    for s in pr["students"]:
        L.append(f"| [{s['name']}](#{anchor(s['name'])}) | {s['done']}/{s['total']} | "
                 f"`{bar(s['done'], s['total'])}` {round(100*s['done']/s['total'])}% |")
    L += [f"| **Всего** | **{pr['done']}/{pr['total']}** | `{bar(pr['done'], pr['total'])}` {pct}% |", ""]

    L += ["## Проекты", ""]
    for s in pr["students"]:
        L += [f"### {s['name']}", "", f"Папка: [`{s['path']}/`]({s['path']}) · сдано **{s['done']}/{s['total']}**", ""]
        for p in s["projects"]:
            mark = "x" if p["done"] else " "
            meta = [f"[📁 папка]({p['path']})"]
            if p["done"]:
                if p["pr"]:
                    meta.append(f"[PR #{p['pr']}]({p['pr_url']})")
                if p["by"]:
                    meta.append(f"@{p['by']}" if p.get("by_login") else p["by"])
                if p["submitted_at"]:
                    meta.append(f"принят {fmt_date(p['submitted_at'])}")
            L.append(f"- [{mark}] **{p['n']}. {p['title']}** — " + " · ".join(meta))
        L.append("")

    L += [
        "## Как сдать проект",
        "",
        "1. Сделайте **Fork** этого репозитория (или ветку, если вы добавлены в коллабораторы).",
        f"2. Положите файлы проекта **в свою папку проекта**: `{pdir}/<Фамилия_Имя>/<N_название>/`. "
        "Там уже лежит `TASK.md` с заданием — его не трогайте.",
        "3. Откройте **Pull Request** в ветку `main`.",
        "4. После того как PR примут, галка в этом README и на сайте поставится **автоматически** (≈1–2 минуты).",
        "",
        "## Что должно быть в отчёте",
        "",
        "| Раздел | Обязательно раскрыть |",
        "|---|---|",
    ]
    L += [f"| {r['section']} | {r['required']} |" for r in pr["report_template"]]
    L.append("")
    return "\n".join(L)


def anchor(text):
    a = text.strip().lower()
    a = re.sub(r"[^\w\- ]", "", a, flags=re.UNICODE)
    return a.replace(" ", "-")


if __name__ == "__main__":
    main()
