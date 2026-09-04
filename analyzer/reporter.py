from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

console = Console()


# ============================================================
# HEADER
# ============================================================

def print_header():
    console.print()

    console.print(
        Panel(
            "[bold cyan]🔐 LEAKGUARD[/bold cyan]\n"
            "[dim]Python Resource Security Analyzer[/dim]",
            border_style="cyan",
            expand=False,
            padding=(0, 1),
        )
    )


# ============================================================
# RESOLUTION
# ============================================================

def get_resolution(leak):
    fix = leak.get("fix", {})

    if fix.get("summary"):
        return fix["summary"]

    variable = leak["variable"]

    reason = leak.get("reason", "").lower()

    if "return" in reason:
        return (
            f"Close '{variable}' before returning, "
            f"or use a 'with open(...)' block."
        )

    if "exception" in reason:
        return (
            f"Make sure '{variable}' is closed even when "
            f"an exception occurs. Use 'finally' or 'with'."
        )

    return (
        f"Close '{variable}' after its final use, "
        f"or use a 'with open(...)' block."
    )


# ============================================================
# SUGGESTED FIX
# ============================================================

def get_suggested_fix(leak):
    fix = leak.get("fix", {})

    if fix.get("example"):
        return fix["example"]

    variable = leak["variable"]

    return f"{variable}.close()"


# ============================================================
# EXECUTION PATH
# ============================================================

def print_execution_path(leak):
    path = leak.get("path", [])

    if not path:
        console.print(
            "[dim]No execution path information available.[/dim]"
        )
        return

    for index, step in enumerate(path):

        if index == 0:
            console.print(f"  [white]{step}[/white]")
        else:
            console.print(
                f"  [cyan]↓[/cyan] [white]{step}[/white]"
            )


# ============================================================
# MAIN REPORT
# ============================================================

def print_report(filename, leaks):

    print_header()

    # ========================================================
    # NO LEAKS
    # ========================================================

    if not leaks:

        console.print(
            Panel(
                "[bold green]✅ NO RESOURCE LEAKS DETECTED[/bold green]\n\n"
                "[green]All analyzed execution paths appear to "
                "release their tracked resources.[/green]",
                title="[bold green]SECURITY RESULT[/bold green]",
                border_style="green",
                padding=(0, 1),
            )
        )

        console.print(
            f"📄 [bold]FILE:[/bold] {filename}"
        )

        console.print(
            "\n[bold green]✔ BUILD PASSED[/bold green]"
        )

        console.print()
        return


    # ========================================================
    # SUMMARY
    # ========================================================

    high = sum(
        1 for leak in leaks
        if leak.get("severity") == "HIGH"
    )

    medium = sum(
        1 for leak in leaks
        if leak.get("severity") == "MEDIUM"
    )

    definite = sum(
        1 for leak in leaks
        if leak.get("certainty") == "DEFINITE"
    )

    possible = sum(
        1 for leak in leaks
        if leak.get("certainty") == "POSSIBLE"
    )

    summary = Table.grid(
        padding=(0, 2)
    )

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

    summary.add_row(
        "✓ DEFINITE",
        str(definite)
    )

    summary.add_row(
        "? POSSIBLE",
        str(possible)
    )

    console.print()

    console.print(
        Panel(
            summary,
            title="[bold]SCAN SUMMARY[/bold]",
            border_style="yellow",
            padding=(0, 1),
        )
    )


    # ========================================================
    # FINDINGS
    # ========================================================

    for index, leak in enumerate(leaks, start=1):

        variable = leak["variable"]
        resource_type = leak["resource_type"]

        open_line = leak["open_line"]
        leak_line = leak["leak_line"]

        severity = leak.get(
            "severity",
            "UNKNOWN"
        )

        certainty = leak.get(
            "certainty",
            "UNKNOWN"
        )

        reason = leak.get(
            "reason",
            "Resource leak detected."
        )

        resolution = get_resolution(leak)
        suggested_fix = get_suggested_fix(leak)


        # ----------------------------------------------------
        # FINDING PANEL
        # ----------------------------------------------------

        finding = Text()

        finding.append(
            f"📍 OPENED: line {open_line}\n",
            style="bold"
        )

        finding.append(
            f"📍 EXIT: line {leak_line}\n"
        )

        finding.append(
            f"🔧 RESOURCE: {resource_type}\n"
        )

        finding.append(
            f"📦 VARIABLE: {variable}\n"
        )

        finding.append(
            f"🚨 SEVERITY: {severity}\n",
            style=(
                "bold red"
                if severity == "HIGH"
                else "bold yellow"
            )
        )

        finding.append(
            f"🔎 CERTAINTY: {certainty}\n\n",
            style="bold"
        )

        finding.append(
            "🔍 REASON\n",
            style="bold yellow"
        )

        finding.append(
            f"{reason}"
        )


        console.print()

        console.print(
            Panel(
                finding,
                title=(
                    f"[bold red]🔴 FINDING #{index} "
                    f"· RESOURCE LEAK[/bold red]"
                ),
                border_style="red",
                padding=(0, 1),
                expand=True,
            )
        )


        # ----------------------------------------------------
        # EXECUTION PATH
        # ----------------------------------------------------

        path_text = Text()

        path = leak.get("path", [])

        if path:

            for i, step in enumerate(path):

                if i > 0:
                    path_text.append(
                        "\n      ↓\n",
                        style="cyan"
                    )

                path_text.append(
                    f"  {step}"
                )

        else:

            path_text.append(
                "  Execution path not available.",
                style="dim"
            )


        console.print(
            Panel(
                path_text,
                title="[bold cyan]🧭 EXECUTION PATH[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
                expand=True,
            )
        )


        # ----------------------------------------------------
        # RESOLUTION
        # ----------------------------------------------------

        console.print(
            Panel(
                resolution,
                title="[bold green]🛠 RESOLUTION[/bold green]",
                border_style="green",
                padding=(0, 1),
                expand=True,
            )
        )


        # ----------------------------------------------------
        # SUGGESTED FIX
        # ----------------------------------------------------

        fix = leak.get("fix", {})

        fix_text = Text()

        if fix.get("strategy"):
            fix_text.append(
                f"Strategy: {fix['strategy']}\n"
            )

        if fix.get("confidence"):
            fix_text.append(
                f"Confidence: {fix['confidence']}\n\n",
                style="bold"
            )

        fix_text.append(
            "Recommended code:\n",
            style="bold cyan"
        )

        fix_text.append(
            suggested_fix
        )

        if fix.get("why"):

            fix_text.append(
                "\n\nWhy this fix:\n",
                style="bold green"
            )

            fix_text.append(
                fix["why"]
            )

        if fix.get("risk"):

            fix_text.append(
                "\n\nImportant:\n",
                style="bold yellow"
            )

            fix_text.append(
                fix["risk"]
            )


        console.print(
            Panel(
                fix_text,
                title="[bold cyan]💡 SUGGESTED FIX[/bold cyan]",
                border_style="cyan",
                padding=(0, 1),
                expand=True,
            )
        )


    # ========================================================
    # BUILD FAILED
    # ========================================================

    console.print()

    console.print(
        Panel(
            "[bold red]⚠️ BUILD FAILED[/bold red]\n\n"
            f"{len(leaks)} resource leak(s) require attention.",
            border_style="red",
            padding=(0, 1),
            expand=False,
        )
    )

    console.print()