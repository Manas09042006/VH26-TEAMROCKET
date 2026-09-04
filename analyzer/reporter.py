def print_report(filename, leaks):
    print()
    print("=" * 60)
    print("                    LEAKGUARD")
    print("=" * 60)
    print()

    print(f"File: {filename}")
    print()

    if not leaks:
        print("✅ No resource leaks detected.")
        print()
        return

    print(
        f"❌ {len(leaks)} resource leak(s) detected."
    )

    print()

    for number, leak in enumerate(leaks, start=1):

        print(f"[{number}] RESOURCE LEAK")

        print(
            f"    Variable     : {leak['variable']}"
        )

        print(
            f"    Resource     : {leak['resource_type']}"
        )

        print(
            f"    Opened at    : line {leak['open_line']}"
        )

        print(
            f"    Detected at  : line {leak['leak_line']}"
        )

        print(
            f"    Reason       : {leak['reason']}"
        )

        print()

    print("=" * 60)
    print("BUILD FAILED")
    print("=" * 60)