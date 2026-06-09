"""
일일 보고서 생성 후 Windows 토스트 알림 발송.
daily_report.py 실행 후 호출하거나 단독 실행 가능.
사용법: python scripts/notify_report.py [--date YYYY-MM-DD]
"""
import subprocess
import sys
import argparse
from datetime import date
from pathlib import Path


def notify_windows(title: str, message: str):
    """Windows 토스트 알림 (PowerShell BurntToast 또는 기본 알림)."""
    if sys.platform != 'win32':
        return
    # PS 스크립트 인젝션 방어: 큰따옴표 이스케이프
    safe_title = title.replace('"', '`"')
    safe_message = message.replace('"', '`"')
    ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.BalloonTipTitle = "{safe_title}"
$notify.BalloonTipText = "{safe_message}"
$notify.Visible = $true
$notify.ShowBalloonTip(8000)
Start-Sleep -Seconds 9
$notify.Dispose()
"""
    subprocess.Popen(
        ["powershell", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", ps_script],
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
    )


def open_report(report_path: Path):
    """보고서를 기본 브라우저로 열기."""
    subprocess.Popen(["start", "", str(report_path)], shell=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(date.today()))
    parser.add_argument("--open", action="store_true", help="보고서 브라우저로 열기")
    parser.add_argument("--no-notify", action="store_true")
    # 직접 알림 제목·내용 지정 시 사용 (api_server.py 등 외부 호출용)
    parser.add_argument("--title", default="", help="알림 제목 (지정 시 보고서 생성 생략)")
    parser.add_argument("--message", default="", help="알림 내용 (지정 시 보고서 생성 생략)")
    args = parser.parse_args()

    # --title / --message 가 직접 지정된 경우: 즉시 알림만 발송하고 종료
    if args.title or args.message:
        title = args.title or "에이전트 알림"
        message = args.message or ""
        if not args.no_notify:
            notify_windows(title, message)
        print(f"알림 발송 완료: {title} / {message}")
        return

    repo = Path(__file__).parent.parent
    report = repo / "reports" / f"{args.date}.html"

    # 보고서 없으면 생성
    if not report.exists():
        try:
            subprocess.run([sys.executable, str(repo / "scripts" / "daily_report.py"),
                            "--date", args.date], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"[notify_report] 보고서 생성 실패: {e}", file=sys.stderr)
            return

    if not args.no_notify:
        # 보고서 내용 파싱해서 요약
        try:
            text = report.read_text(encoding="utf-8")
            import re
            total = len(re.findall(r'"log-entry"', text))
            done  = len(re.findall(r'status-done', text))
            rate  = f"{done/total*100:.0f}%" if total else "N/A"
            msg   = f"{args.date} 보고서 생성 완료\n총 {total}건 처리 · 완료율 {rate}"
        except Exception:
            msg = f"{args.date} 일일 보고서가 생성됐습니다."

        notify_windows("Your Organization 에이전트 일일 보고서", msg)

    if args.open:
        open_report(report)

    print(f"알림 발송 완료: {report}")


if __name__ == "__main__":
    main()
