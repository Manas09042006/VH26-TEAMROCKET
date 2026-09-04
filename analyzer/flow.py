import ast
import copy

from analyzer.resource import Resource
from analyzer.detector import (
    is_resource_creator,
    is_resource_releaser,
)


class FlowOutcome:
    """
    Represents one possible control-flow result.

    kind:
        normal    -> execution continues
        return    -> function returned
        raise     -> exception escaped
        exception -> possible exception path
    """

    def __init__(self, state, kind="normal", line=None, path=None):
        self.state = state
        self.kind = kind
        self.line = line
        self.path = path or []


class FlowAnalyzer:

    def __init__(self):
        self.leaks = []

    # =========================================================
    # ENTRY POINT
    # =========================================================

    def analyze(self, tree):

        self.leaks = []

        for node in tree.body:

            if isinstance(node, ast.FunctionDef):

                self.analyze_function(node)

        return self._deduplicate_leaks()

    # =========================================================
    # FUNCTION ANALYSIS
    # =========================================================

    def analyze_function(self, function_node):

        initial_state = {}

        outcomes = self.analyze_block(
            function_node.body,
            initial_state,
            path=[]
        )

        for outcome in outcomes:

            for resource in outcome.state.values():

                if not resource.closed:

                    self._record_leak(
                        resource,
                        outcome,
                        function_node
                    )

    # =========================================================
    # BLOCK ANALYSIS
    # =========================================================

    def analyze_block(self, statements, state, path=None):

        path = path or []

        outcomes = [
            FlowOutcome(
                state=copy.deepcopy(state),
                kind="normal",
                path=path.copy()
            )
        ]

        for statement in statements:

            next_outcomes = []

            for outcome in outcomes:

                # Once execution has returned or raised,
                # normal statements after it are unreachable.
                if outcome.kind != "normal":
                    next_outcomes.append(outcome)
                    continue

                statement_results = self.analyze_statement(
                    statement,
                    outcome.state,
                    outcome.path
                )

                next_outcomes.extend(statement_results)

            outcomes = next_outcomes

        return outcomes

    # =========================================================
    # STATEMENT ANALYSIS
    # =========================================================

    def analyze_statement(self, node, state, path=None):

        path = path or []

        # =====================================================
        # RESOURCE CREATION
        # =====================================================

        if isinstance(node, ast.Assign):

            if is_resource_creator(node.value):

                new_state = copy.deepcopy(state)

                for target in node.targets:

                    if isinstance(target, ast.Name):

                        resource = Resource(
                            variable=target.id,
                            resource_type="file",
                            open_line=node.lineno
                        )

                        new_state[target.id] = resource

                return [
                    FlowOutcome(
                        state=new_state,
                        kind="normal",
                        path=path + [
                            f"resource '{self._assigned_name(node)}' "
                            f"opened at line {node.lineno}"
                        ]
                    )
                ]

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy()
                )
            ]

        # =====================================================
        # RESOURCE RELEASE
        # =====================================================

        if isinstance(node, ast.Expr):

            if is_resource_releaser(node.value):

                new_state = copy.deepcopy(state)

                call = node.value

                if isinstance(call.func, ast.Attribute):

                    variable = call.func.value

                    if isinstance(variable, ast.Name):

                        variable_name = variable.id

                        if variable_name in new_state:

                            new_state[
                                variable_name
                            ].close()

                return [
                    FlowOutcome(
                        state=new_state,
                        kind="normal",
                        path=path + [
                            f"resource released at line {node.lineno}"
                        ]
                    )
                ]

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy()
                )
            ]

        # =====================================================
        # RETURN
        # =====================================================

        if isinstance(node, ast.Return):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="return",
                    line=node.lineno,
                    path=path + [
                        f"return at line {node.lineno}"
                    ]
                )
            ]

        # =====================================================
        # RAISE
        # =====================================================

        if isinstance(node, ast.Raise):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="raise",
                    line=node.lineno,
                    path=path + [
                        f"exception raised at line {node.lineno}"
                    ]
                )
            ]

        # =====================================================
        # IF / ELSE
        # =====================================================

        if isinstance(node, ast.If):

            return self.analyze_if(
                node,
                state,
                path
            )

        # =====================================================
        # TRY / EXCEPT / ELSE / FINALLY
        # =====================================================

        if isinstance(node, ast.Try):

            return self.analyze_try(
                node,
                state,
                path
            )

        # =====================================================
        # NESTED FUNCTION
        # =====================================================

        if isinstance(node, ast.FunctionDef):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy()
                )
            ]

        # =====================================================
        # DEFAULT
        # =====================================================

        return [
            FlowOutcome(
                state=copy.deepcopy(state),
                kind="normal",
                path=path.copy()
            )
        ]

    # =========================================================
    # IF ANALYSIS
    # =========================================================

    def analyze_if(self, node, state, path):

        # -----------------------------------------------------
        # TRUE BRANCH
        # -----------------------------------------------------

        true_state = copy.deepcopy(state)

        true_outcomes = self.analyze_block(
            node.body,
            true_state,
            path + [
                f"if branch at line {node.lineno}"
            ]
        )

        # -----------------------------------------------------
        # FALSE BRANCH
        # -----------------------------------------------------

        false_state = copy.deepcopy(state)

        if node.orelse:

            false_outcomes = self.analyze_block(
                node.orelse,
                false_state,
                path + [
                    f"else branch at line {node.lineno}"
                ]
            )

        else:

            false_outcomes = [
                FlowOutcome(
                    state=false_state,
                    kind="normal",
                    path=path + [
                        f"if condition false at line {node.lineno}"
                    ]
                )
            ]

        return true_outcomes + false_outcomes

    # =========================================================
    # TRY / EXCEPT / ELSE / FINALLY
    # =========================================================

    def analyze_try(self, node, state, path):

        try_path = path + [
            f"try block at line {node.lineno}"
        ]

        # -----------------------------------------------------
        # 1. ANALYZE TRY BODY
        # -----------------------------------------------------

        try_outcomes = self.analyze_block(
            node.body,
            copy.deepcopy(state),
            try_path
        )

        normal_try_outcomes = [
            outcome
            for outcome in try_outcomes
            if outcome.kind == "normal"
        ]

        explicit_raise_outcomes = [
            outcome
            for outcome in try_outcomes
            if outcome.kind == "raise"
        ]

        # -----------------------------------------------------
        # 2. MODEL POSSIBLE IMPLICIT EXCEPTIONS
        #
        # Any expression inside a try block can potentially
        # raise an exception.
        #
        # Example:
        #
        #     data = f.read()
        #
        # There is no explicit `raise`, but read() can fail.
        #
        # We therefore create a conservative exception path.
        # -----------------------------------------------------

        possible_exception_outcomes = []

        if node.handlers:

            for outcome in normal_try_outcomes:

                possible_exception_outcomes.append(
                    FlowOutcome(
                        state=copy.deepcopy(outcome.state),
                        kind="exception",
                        line=node.lineno,
                        path=outcome.path + [
                            "possible exception from try block"
                        ]
                    )
                )

        # Explicit raise paths.

        for outcome in explicit_raise_outcomes:

            possible_exception_outcomes.append(
                FlowOutcome(
                    state=copy.deepcopy(outcome.state),
                    kind="exception",
                    line=outcome.line,
                    path=outcome.path
                )
            )

        # -----------------------------------------------------
        # 3. NORMAL PATH → ELSE
        # -----------------------------------------------------

        normal_after_try = []

        for outcome in normal_try_outcomes:

            if node.orelse:

                else_outcomes = self.analyze_block(
                    node.orelse,
                    copy.deepcopy(outcome.state),
                    outcome.path + [
                        f"else block at line "
                        f"{node.orelse[0].lineno}"
                    ]
                )

                normal_after_try.extend(
                    else_outcomes
                )

            else:

                normal_after_try.append(outcome)

        # -----------------------------------------------------
        # 4. EXCEPTION PATH → EXCEPT
        # -----------------------------------------------------

        exception_after_try = []

        if node.handlers:

            for exception_outcome in possible_exception_outcomes:

                for handler in node.handlers:

                    handler_name = self._handler_name(
                        handler
                    )

                    handler_outcomes = self.analyze_block(
                        handler.body,
                        copy.deepcopy(
                            exception_outcome.state
                        ),
                        exception_outcome.path + [
                            f"except {handler_name} "
                            f"at line {handler.lineno}"
                        ]
                    )

                    exception_after_try.extend(
                        handler_outcomes
                    )

        else:

            # No exception handler.
            #
            # The exception leaves the current function/block.

            exception_after_try = [
                FlowOutcome(
                    state=copy.deepcopy(
                        outcome.state
                    ),
                    kind="raise",
                    line=outcome.line,
                    path=outcome.path
                )
                for outcome in possible_exception_outcomes
            ]

        # -----------------------------------------------------
        # 5. COMBINE ALL PATHS
        # -----------------------------------------------------

        all_outcomes = (
            normal_after_try +
            exception_after_try
        )

        # -----------------------------------------------------
        # 6. FINALLY
        #
        # finally executes regardless of:
        #
        #   normal execution
        #   return
        #   exception
        #   raise
        #
        # Therefore this is where resource cleanup is guaranteed.
        # -----------------------------------------------------

        if node.finalbody:

            final_outcomes = []

            for outcome in all_outcomes:

                final_results = self.analyze_block(
                    node.finalbody,
                    copy.deepcopy(
                        outcome.state
                    ),
                    outcome.path + [
                        f"finally block at line "
                        f"{node.finalbody[0].lineno}"
                    ]
                )

                for final_result in final_results:

                    # If finally itself does not terminate,
                    # preserve the original control-flow result.

                    if final_result.kind == "normal":

                        final_result.kind = outcome.kind

                        if final_result.line is None:
                            final_result.line = outcome.line

                    final_outcomes.append(
                        final_result
                    )

            return final_outcomes

        return all_outcomes

    # =========================================================
    # LEAK DETECTION
    # =========================================================

    def _record_leak(
        self,
        resource,
        outcome,
        function_node
    ):

        # -----------------------------------------------------
        # RETURN PATH
        # -----------------------------------------------------

        if outcome.kind == "return":

            reason = (
                f"Resource '{resource.variable}' is still open "
                f"when the function returns at line "
                f"{outcome.line}."
            )

            severity = "HIGH"
            certainty = "DEFINITE"

        # -----------------------------------------------------
        # EXPLICIT EXCEPTION
        # -----------------------------------------------------

        elif outcome.kind == "raise":

            reason = (
                f"Resource '{resource.variable}' remains open "
                f"when an exception escapes at line "
                f"{outcome.line}."
            )

            severity = "HIGH"
            certainty = "DEFINITE"

        # -----------------------------------------------------
        # POSSIBLE EXCEPTION
        # -----------------------------------------------------

        elif outcome.kind == "exception":

            reason = (
                f"Resource '{resource.variable}' may remain open "
                f"when an exception leaves the current "
                f"control-flow path."
            )

            severity = "HIGH"
            certainty = "POSSIBLE"

        # -----------------------------------------------------
        # NORMAL FUNCTION END
        # -----------------------------------------------------

        else:

            reason = (
                f"Resource '{resource.variable}' was opened at "
                f"line {resource.open_line}, but no release "
                f"operation was detected before the function "
                f"completed."
            )

            severity = "MEDIUM"
            certainty = "DEFINITE"

        # -----------------------------------------------------
        # CREATE FINDING
        # -----------------------------------------------------

        leak = {
            "variable": resource.variable,
            "resource_type": resource.resource_type,
            "open_line": resource.open_line,
            "leak_line": (
                outcome.line
                or function_node.end_lineno
            ),
            "reason": reason,
            "severity": severity,
            "certainty": certainty,
            "path": outcome.path,
        }

        # Generate context-aware remediation.

        leak["fix"] = self._build_fix(
            leak
        )

        self.leaks.append(leak)

    # =========================================================
    # CONTEXT-AWARE FIX ENGINE
    # =========================================================

    def _build_fix(self, leak):

        variable = leak["variable"]
        certainty = leak.get(
            "certainty",
            "UNKNOWN"
        )

        # -----------------------------------------------------
        # RETURN LEAK
        # -----------------------------------------------------

        if (
            "returns" in leak["reason"]
            and certainty == "DEFINITE"
        ):

            return {
                "strategy": "context_manager",
                "confidence": "HIGH",

                "summary": (
                    f"Use a 'with open(...)' context manager "
                    f"for '{variable}' so Python automatically "
                    f"releases the file before the function "
                    f"returns."
                ),

                "example": (
                    f"with open(<path>, <mode>) as {variable}:\n"
                    f"    # use {variable} here\n"
                    f"    ..."
                ),

                "why": (
                    f"The analyzer found a definite return path "
                    f"where '{variable}' is still open."
                ),

                "risk": (
                    "Manually inserting .close() immediately "
                    "before every return can miss other "
                    "exceptional paths."
                ),
            }

        # -----------------------------------------------------
        # EXPLICIT EXCEPTION
        # -----------------------------------------------------

        if (
            "exception" in leak["reason"].lower()
            and certainty == "DEFINITE"
        ):

            return {
                "strategy": "finally_or_context_manager",
                "confidence": "HIGH",

                "summary": (
                    f"Guarantee cleanup of '{variable}' using "
                    f"a finally block or, preferably, a "
                    f"context manager."
                ),

                "example": (
                    f"{variable} = open(<path>, <mode>)\n"
                    f"try:\n"
                    f"    # use {variable}\n"
                    f"    ...\n"
                    f"finally:\n"
                    f"    {variable}.close()"
                ),

                "why": (
                    f"An exception path can leave the resource "
                    f"'{variable}' open."
                ),

                "risk": (
                    "Closing only in the normal execution path "
                    "does not guarantee cleanup after exceptions."
                ),
            }

        # -----------------------------------------------------
        # POSSIBLE EXCEPTION
        # -----------------------------------------------------

        if (
            "exception" in leak["reason"].lower()
            and certainty == "POSSIBLE"
        ):

            return {
                "strategy": "context_manager",
                "confidence": "HIGH",

                "summary": (
                    f"Protect '{variable}' with a context "
                    f"manager or finally block."
                ),

                "example": (
                    f"with open(<path>, <mode>) as {variable}:\n"
                    f"    # operations that may raise\n"
                    f"    ..."
                ),

                "why": (
                    f"The analyzer conservatively identified "
                    f"an exception path where '{variable}' "
                    f"could remain live."
                ),

                "risk": (
                    "The exception is a possible path rather "
                    "than proof that the operation will fail "
                    "at runtime."
                ),
            }

        # -----------------------------------------------------
        # NORMAL PATH LEAK
        # -----------------------------------------------------

        return {
            "strategy": "explicit_close_or_context_manager",
            "confidence": "MEDIUM",

            "summary": (
                f"Release '{variable}' after its final use, "
                f"or use a context manager."
            ),

            "example": (
                f"{variable}.close()"
            ),

            "why": (
                f"No release operation for '{variable}' "
                f"was detected on the analyzed path."
            ),

            "risk": (
                "Leaving the resource open can consume file "
                "descriptors and eventually cause resource "
                "exhaustion."
            ),
        }

    # =========================================================
    # HELPERS
    # =========================================================

    @staticmethod
    def _assigned_name(node):

        for target in node.targets:

            if isinstance(target, ast.Name):
                return target.id

        return "resource"

    @staticmethod
    def _handler_name(handler):

        if handler.type is None:
            return "bare except"

        if isinstance(handler.type, ast.Name):
            return handler.type.id

        if isinstance(handler.type, ast.Attribute):
            return handler.type.attr

        return "exception handler"

    # =========================================================
    # DUPLICATE REMOVAL
    # =========================================================

    def _deduplicate_leaks(self):

        unique = []
        seen = set()

        for leak in self.leaks:

            key = (
                leak["variable"],
                leak["resource_type"],
                leak["open_line"],
                leak["leak_line"],
                leak["reason"],
            )

            if key not in seen:

                seen.add(key)
                unique.append(leak)

        return unique