from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def get_resolution(leak):
    reason = leak["reason"].lower()

    if "returns" in reason:
        return (
            f"Close '{leak['variable']}' before the function returns, "
            "or use a 'with open(...)' block."
        )

    if "raises" in reason or "exception" in reason:
        return (
            f"Make sure '{leak['variable']}' is closed even when an "
            "exception occurs. Use 'finally' or preferably 'with open(...)'."
        )

    return (
        f"Close '{leak['variable']}' after you finish using it. "
        "Using 'with open(...)' is recommended."
    )


def get_suggested_fix(leak):
    """
    Generate a suggested fix.
    """

    variable = leak["variable"]
    reason = leak["reason"].lower()

    # Case 1: Resource is leaked because of return
    if "returns" in reason:
        return (
            f"# Close the resource before returning\n"
            f"{variable}.close()\n"
            f"return data"
        )

    # Case 2: Resource remains open when exception occurs
    if "raises" in reason or "exception" in reason:
        return (
            f"try:\n"
            f"    # use {variable} here\n"
            f"    data = {variable}.read()\n"
            f"finally:\n"
            f"    {variable}.close()"
        )

    # Default case
    return (
        f"# Close the resource after use\n"
        f"{variable}.close()"
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


def print_report(filename, leaks):
    print_header()

# NO LEAKS

    if not leaks:
        console.print(
            Panel(
                "[bold green]✅ NO RESOURCE LEAKS DETECTED[/bold green]\n\n"
                "[green]All analyzed execution paths appear to "
                "release their tracked resources.[/green]",
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

    # -------------------------
    # SUMMARY
    # -------------------------

    summary = Table.grid(padding=(0, 2))

    summary.add_row(
        "📄 FILE",
        f"[bold]{filename}[/bold]"
    )

    summary.add_row(
        "📊 RESULT",
        f"[bold red]{len(leaks)} issue(s) found[/bold red]"
    )

    console.print(
        Panel(
            summary,
            title="[bold]SCAN SUMMARY[/bold]",
            border_style="yellow",
        )
    )

    console.print()

# FINDINGS

    for index, leak in enumerate(leaks, start=1):

        resolution = get_resolution(leak)
        suggested_fix = get_suggested_fix(leak)

        finding = Text()

        finding.append(
            f"📍 LINE: {leak['open_line']}\n",
            style="bold"
        )

        finding.append(
            f"🔧 RESOURCE: {leak['resource_type']}\n"
        )

        finding.append(
            f"📦 VARIABLE: {leak['variable']}\n\n"
        )

        finding.append(
            "🔍 REASON\n",
            style="bold yellow"
        )

        finding.append(
            f"{leak['reason']}\n\n"
        )

        finding.append(
            "🛠️  RESOLVE\n",
            style="bold green"
        )

        finding.append(
            f"{resolution}\n\n"
        )

        finding.append(
            "💡 SUGGESTED FIX\n",
            style="bold cyan"
        )

        finding.append(
            suggested_fix
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

        console.print()

# BUILD FAILED

    console.print(
        Panel(
            f"[bold red]⚠️  BUILD FAILED[/bold red]\n\n"
            f"{len(leaks)} resource leak(s) require attention.",
            border_style="red",
            expand=False,
        )
    )

    console.print()