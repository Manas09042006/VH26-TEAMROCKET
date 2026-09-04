import argparse
import os

from analyzer.parser import parse_file
from analyzer.flow import FlowAnalyzer
from analyzer.reporter import print_report

from agent.events import EventReporter


BACKEND_URL = os.getenv(
    "LEAKGUARD_BACKEND_URL",
    "http://127.0.0.1:8000"
)

AGENT_ID = os.getenv(
    "LEAKGUARD_AGENT_ID",
    "agent-test-001"
)


def report_scan_result(filename, leaks):
    reporter = EventReporter(
        backend_url=BACKEND_URL,
        agent_id=AGENT_ID
    )

    reporter.send_scan_result(
        filename=filename,
        leaks=leaks
    )


def main():
    parser = argparse.ArgumentParser(
        description="LeakGuard Python Resource Leak Analyzer"
    )

    parser.add_argument(
        "file",
        help="Python file to analyze"
    )

    args = parser.parse_args()

    try:
        tree = parse_file(args.file)

    except FileNotFoundError:
        print(f"❌ File not found: {args.file}")
        return 1

    except SyntaxError as error:
        print("❌ Python syntax error")
        print(f"Line {error.lineno}: {error.msg}")
        return 1

    analyzer = FlowAnalyzer()

    leaks = analyzer.analyze(tree)

    print_report(args.file, leaks)

    # Report the scan to the monitoring backend.
    # Failure to report must never break LeakGuard itself.
    report_scan_result(
        filename=args.file,
        leaks=leaks
    )

    if leaks:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())