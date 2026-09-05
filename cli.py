import argparse
import json
from pathlib import Path

from analyzer.parser import parse_file
from analyzer.flow import FlowAnalyzer
from analyzer.reporter import print_report


def find_python_files(path):
    path = Path(path)

    if path.is_file():
        return [path]

    return [
        file
        for file in path.rglob("*.py")
        if ".git" not in file.parts
        and "__pycache__" not in file.parts
    ]


def analyze_file(filename):
    try:
        tree = parse_file(filename)

    except SyntaxError as error:
        return {
            "file": str(filename),
            "status": "ERROR",
            "error": f"Line {error.lineno}: {error.msg}",
            "leaks": []
        }

    except Exception as error:
        return {
            "file": str(filename),
            "status": "ERROR",
            "error": str(error),
            "leaks": []
        }

    analyzer = FlowAnalyzer()
    leaks = analyzer.analyze(tree)

    return {
        "file": str(filename),
        "status": "FAILED" if leaks else "PASSED",
        "leaks": leaks
    }


def main():

    parser = argparse.ArgumentParser(
        description="LeakGuard Python Resource Security Analyzer"
    )

    parser.add_argument(
        "path",
        help="Python file or directory to analyze"
    )

    parser.add_argument(
        "--format",
        choices=["rich", "json"],
        default="rich",
        help="Output format"
    )

    args = parser.parse_args()

    files = find_python_files(args.path)

    if not files:
        print(f"No Python files found in: {args.path}")
        return 0

    results = []

    for filename in files:
        result = analyze_file(filename)
        results.append(result)

    total_leaks = sum(
        len(result["leaks"])
        for result in results
    )

    errors = [
        result
        for result in results
        if result["status"] == "ERROR"
    ]

    # JSON OUTPUT
    if args.format == "json":

        output = {
            "tool": "LeakGuard",
            "status": (
                "FAILED"
                if total_leaks or errors
                else "PASSED"
            ),
            "files_scanned": len(files),
            "total_leaks": total_leaks,
            "errors": len(errors),
            "results": results
        }

        print(
            json.dumps(
                output,
                indent=2,
                default=str
            )
        )

    # RICH OUTPUT
    else:

        for result in results:

            if result["status"] == "ERROR":

                print(f"❌ {result['file']}")
                print(f"   {result['error']}")

                continue

            print_report(
                result["file"],
                result["leaks"]
            )

        print()
        print("=" * 60)
        print(f"Files scanned : {len(files)}")
        print(f"Leaks found   : {total_leaks}")
        print(f"Errors        : {len(errors)}")
        print("=" * 60)

    # Exit code
    if total_leaks or errors:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())