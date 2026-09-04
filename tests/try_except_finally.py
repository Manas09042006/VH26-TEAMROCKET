from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def get_resolution(leak):

    fix = leak.get("fix", {})

    strategy = fix.get("strategy")

    if strategy == "context_manager":

        return (
            f"Replace manual resource management for "
            f"'{leak['variable']}' with a 'with open(...)' "
            f"context manager."
        )

    if strategy == "finally_or_context_manager":

        return (
            f"Guarantee cleanup for '{leak['variable']}' using "
            f"'finally', or preferably a 'with open(...)' "
            f"context manager."
        )

    return (
        f"Close '{leak['variable']}' after its final use. "
        f"A context manager is preferred for file resources."
    )


def get_suggested_fix(leak):

    fix = leak.get("fix", {})

    example = fix.get("example")

    if example:
        return example

    return (
        f"{leak['variable']}.close()"
    )


def print_header():

    console.print()

    console.print(
        Panel(
            "[bold cyan]🔐 LEAKGUARD[/bold cyan]\n"
            "[dim]Python Resource Security Analyzer[/dim]",
            border_style="cyan",
            expand=False,
        )
    )

    console.print()


def print_path(leak):

    path = leak.get("path", [])

    if not path:
        console.print(
            "[dim]Execution path information unavailable.[/dim]"
        )
        return

    for index, step in enumerate(path):

        connector = "  ↓ " if index > 0 else ""

        console.print(
            f"[dim]{connector}[/dim][white]{step}[/white]"
        )


def print_report(filename, leaks):

    print_header()

    # ---------------------------------------------------------
    # SAFE
    # ---------------------------------------------------------

    if not leaks:

        console.print(
            Panel(
                "[bold green]✅ NO RESOURCE LEAKS DETECTED[/bold green]\n\n"
                "[green]"
                "All analyzed execution paths appear to release "
                "their tracked resources."
                "[/green]",
                title="SECURITY RESULT",
                border_style="green",
            )
        )

        console.print(
            f"\n📄 [bold]FILE:[/bold] {filename}"
        )

        console.print(
            "\n[bold green]✔ BUILD PASSED[/bold green]"
        )

        console.print()

        return

    # ---------------------------------------------------------
    # SUMMARY
    # ---------------------------------------------------------

    high = sum(
        1 for leak in leaks
        if leak.get("severity") == "HIGH"
    )

    medium = sum(
        1 for leak in leaks
        if leak.get("severity") == "MEDIUM"
    )

    summary = Table.grid(padding=(0, 2))

    summary.add_row(
        "📄 FILE",
        f"[bold]{filename}[/bold]"
    )

    summary.add_row(
        "📊 RESULT",
        f"[bold red]{len(leaks)} issue(s) found[/bold red]"
    )

    summary.add_row(
        "🔴 HIGH",
        str(high)
    )

    summary.add_row(
        "🟡 MEDIUM",
        str(medium)
    )

    console.print(
        Panel(
            summary,
            title="[bold]SCAN SUMMARY[/bold]",
            border_style="yellow",
        )
    )

    console.print()

    # ---------------------------------------------------------
    # FINDINGS
    # ---------------------------------------------------------

    for index, leak in enumerate(leaks, start=1):

        resolution = get_resolution(leak)
        suggested_fix = get_suggested_fix(leak)

        finding = Text()

        finding.append(
            f"📍 OPENED: line {leak['open_line']}\n",
            style="bold",
        )

        finding.append(
            f"📍 LEAK PATH ENDS: line {leak['leak_line']}\n"
        )

        finding.append(
            f"🔧 RESOURCE: {leak['resource_type']}\n"
        )

        finding.append(
            f"📦 VARIABLE: {leak['variable']}\n"
        )

        finding.append(
            f"🚨 SEVERITY: {leak.get('severity', 'UNKNOWN')}\n\n",
            style="bold red"
            if leak.get("severity") == "HIGH"
            else "bold yellow",
        )

        finding.append(
            "🔍 WHY THIS IS A PROBLEM\n",
            style="bold yellow",
        )

        finding.append(
            f"{leak['reason']}\n\n"
        )

        finding.append(
            "🧭 EXECUTION PATH\n",
            style="bold cyan",
        )

        console.print(
            Panel(
                finding,
                title=(
                    f"[bold red]"
                    f"🔴 FINDING #{index} · RESOURCE LEAK"
                    f"[/bold red]"
                ),
                border_style="red",
            )
        )

        print_path(leak)

        console.print()

        # -----------------------------------------------------
        # RESOLUTION
        # -----------------------------------------------------

        console.print(
            Panel(
                resolution,
                title="[bold green]🛠 RESOLUTION[/bold green]",
                border_style="green",
            )
        )

        # -----------------------------------------------------
        # FIX
        # -----------------------------------------------------

        fix = leak.get("fix", {})

        fix_text = Text()

        fix_text.append(
            f"Strategy: {fix.get('strategy', 'manual review')}\n",
            style="bold",
        )

        fix_text.append(
            f"Confidence: {fix.get('confidence', 'unknown')}\n\n"
        )

        fix_text.append(
            suggested_fix
        )

        console.print(
            Panel(
                fix_text,
                title="[bold cyan]💡 SUGGESTED FIX[/bold cyan]",
                border_style="cyan",
            )
        )

        console.print()

    # ---------------------------------------------------------
    # BUILD FAILURE
    # ---------------------------------------------------------

    console.print(
        Panel(
            "[bold red]⚠️ BUILD FAILED[/bold red]\n\n"
            f"{len(leaks)} resource leak(s) require attention.",
            border_style="red",
            expand=False,
        )
    )

    console.print()