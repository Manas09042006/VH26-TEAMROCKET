import ast
import copy

from analyzer.resource import Resource
from analyzer.detector import (
    is_resource_creator,
    is_resource_releaser,
)


class FlowOutcome:
    def __init__(self, state, kind="normal", line=None, path=None):
        self.state = state
        self.kind = kind
        self.line = line
        self.path = path or []


class FlowAnalyzer:
    def __init__(self):
        self.leaks = []

    def analyze(self, tree):
        self.leaks = []

        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                self.analyze_function(node)

        return self._deduplicate_leaks()

    # ---------------------------------------------------------
    # FUNCTION ANALYSIS
    # ---------------------------------------------------------

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
                        resource=resource,
                        outcome=outcome,
                        function_node=function_node,
                    )

    # ---------------------------------------------------------
    # BLOCK ANALYSIS
    # ---------------------------------------------------------

    def analyze_block(self, statements, state, path=None):
        path = path or []

        outcomes = [
            FlowOutcome(
                state=copy.deepcopy(state),
                kind="normal",
                path=path.copy(),
            )
        ]

        for statement in statements:

            next_outcomes = []

            for outcome in outcomes:

                if outcome.kind != "normal":
                    next_outcomes.append(outcome)
                    continue

                statement_results = self.analyze_statement(
                    statement,
                    outcome.state,
                    outcome.path,
                )

                next_outcomes.extend(statement_results)

            outcomes = next_outcomes

        return outcomes

    # ---------------------------------------------------------
    # STATEMENT ANALYSIS
    # ---------------------------------------------------------

    def analyze_statement(self, node, state, path=None):
        path = path or []

        # -----------------------------------------------------
        # RESOURCE CREATION
        # -----------------------------------------------------

        if isinstance(node, ast.Assign):

            if is_resource_creator(node.value):

                new_state = copy.deepcopy(state)

                for target in node.targets:

                    if isinstance(target, ast.Name):

                        resource = Resource(
                            variable=target.id,
                            resource_type="file",
                            open_line=node.lineno,
                        )

                        new_state[target.id] = resource

                return [
                    FlowOutcome(
                        state=new_state,
                        kind="normal",
                        path=path + [
                            f"resource '{self._assigned_name(node)}' opened at line {node.lineno}"
                        ],
                    )
                ]

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy(),
                )
            ]

        # -----------------------------------------------------
        # RESOURCE RELEASE
        # -----------------------------------------------------

        if isinstance(node, ast.Expr):

            if is_resource_releaser(node.value):

                new_state = copy.deepcopy(state)

                call = node.value

                if isinstance(call.func, ast.Attribute):

                    variable = call.func.value

                    if isinstance(variable, ast.Name):

                        variable_name = variable.id

                        if variable_name in new_state:

                            new_state[variable_name].close()

                return [
                    FlowOutcome(
                        state=new_state,
                        kind="normal",
                        path=path + [
                            f"resource released at line {node.lineno}"
                        ],
                    )
                ]

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy(),
                )
            ]

        # -----------------------------------------------------
        # RETURN
        # -----------------------------------------------------

        if isinstance(node, ast.Return):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="return",
                    line=node.lineno,
                    path=path + [
                        f"return at line {node.lineno}"
                    ],
                )
            ]

        # -----------------------------------------------------
        # RAISE
        # -----------------------------------------------------

        if isinstance(node, ast.Raise):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="raise",
                    line=node.lineno,
                    path=path + [
                        f"exception raised at line {node.lineno}"
                    ],
                )
            ]

        # -----------------------------------------------------
        # IF
        # -----------------------------------------------------

        if isinstance(node, ast.If):

            return self.analyze_if(
                node,
                state,
                path,
            )

        # -----------------------------------------------------
        # TRY / EXCEPT / ELSE / FINALLY
        # -----------------------------------------------------

        if isinstance(node, ast.Try):

            return self.analyze_try(
                node,
                state,
                path,
            )

        # -----------------------------------------------------
        # NESTED FUNCTION
        # -----------------------------------------------------

        if isinstance(node, ast.FunctionDef):

            return [
                FlowOutcome(
                    state=copy.deepcopy(state),
                    kind="normal",
                    path=path.copy(),
                )
            ]

        # -----------------------------------------------------
        # DEFAULT
        # -----------------------------------------------------

        return [
            FlowOutcome(
                state=copy.deepcopy(state),
                kind="normal",
                path=path.copy(),
            )
        ]

    # ---------------------------------------------------------
    # IF ANALYSIS
    # ---------------------------------------------------------

    def analyze_if(self, node, state, path):

        true_state = copy.deepcopy(state)

        true_outcomes = self.analyze_block(
            node.body,
            true_state,
            path + [
                f"if branch at line {node.lineno}"
            ],
        )

        false_state = copy.deepcopy(state)

        if node.orelse:

            false_outcomes = self.analyze_block(
                node.orelse,
                false_state,
                path + [
                    f"else branch at line {node.lineno}"
                ],
            )

        else:

            false_outcomes = [
                FlowOutcome(
                    state=false_state,
                    kind="normal",
                    path=path + [
                        f"if condition false at line {node.lineno}"
                    ],
                )
            ]

        return true_outcomes + false_outcomes

    # ---------------------------------------------------------
    # TRY ANALYSIS
    # ---------------------------------------------------------

    def analyze_try(self, node, state, path):

        try_path = path + [
            f"try block at line {node.lineno}"
        ]

        # -----------------------------------------------------
        # 1. Analyze TRY body
        # -----------------------------------------------------

        try_outcomes = self.analyze_block(
            node.body,
            copy.deepcopy(state),
            try_path,
        )

        normal_try_outcomes = [
            outcome
            for outcome in try_outcomes
            if outcome.kind == "normal"
        ]

        raised_try_outcomes = [
            outcome
            for outcome in try_outcomes
            if outcome.kind == "raise"
        ]

        # -----------------------------------------------------
        # 2. TRY NORMAL PATH → ELSE
        # -----------------------------------------------------

        normal_after_try = []

        if node.orelse:

            for outcome in normal_try_outcomes:

                else_outcomes = self.analyze_block(
                    node.orelse,
                    copy.deepcopy(outcome.state),
                    outcome.path + [
                        f"else block at line {node.lineno}"
                    ],
                )

                normal_after_try.extend(else_outcomes)

        else:

            normal_after_try = normal_try_outcomes

        # -----------------------------------------------------
        # 3. TRY EXCEPTION PATH → EXCEPT
        # -----------------------------------------------------

        exception_after_try = []

        if node.handlers:

            for raised in raised_try_outcomes:

                for handler in node.handlers:

                    handler_name = self._handler_name(handler)

                    handler_outcomes = self.analyze_block(
                        handler.body,
                        copy.deepcopy(raised.state),
                        raised.path + [
                            f"except {handler_name} at line {handler.lineno}"
                        ],
                    )

                    exception_after_try.extend(
                        handler_outcomes
                    )

        else:

            # No except block.
            # Exception escapes the try statement.
            exception_after_try = raised_try_outcomes

# 4. COMBINE NORMAL + EXCEPTION PATHS
    

        all_outcomes = (
            normal_after_try +
            exception_after_try
        )


        if node.finalbody:

            final_outcomes = []

            for outcome in all_outcomes:

                final_results = self.analyze_block(
                    node.finalbody,
                    copy.deepcopy(outcome.state),
                    outcome.path + [
                        f"finally block at line {node.finalbody[0].lineno}"
                    ],
                )

                for final_result in final_results:

                    # If finally completes normally, preserve
                    # the original control-flow outcome.
                    if final_result.kind == "normal":

                        final_result.kind = outcome.kind

                        if final_result.line is None:
                            final_result.line = outcome.line

                    final_outcomes.append(final_result)

            return final_outcomes

        return all_outcomes


# LEAK RECORDING


    def _record_leak(self, resource, outcome, function_node):

        if outcome.kind == "return":

            reason = (
                f"Resource '{resource.variable}' is still open "
                f"when the function returns at line {outcome.line}."
            )

            severity = "HIGH"

        elif outcome.kind == "raise":

            reason = (
                f"Resource '{resource.variable}' remains open "
                f"when an exception escapes at line {outcome.line}."
            )

            severity = "HIGH"

        else:

            reason = (
                f"Resource '{resource.variable}' was opened at line "
                f"{resource.open_line} but no release was detected "
                f"on this execution path."
            )

            severity = "MEDIUM"

        leak = {
            "variable": resource.variable,
            "resource_type": resource.resource_type,
            "open_line": resource.open_line,
            "leak_line": outcome.line or function_node.end_lineno,
            "reason": reason,
            "severity": severity,
            "path": outcome.path,
        }

        leak["fix"] = self._build_fix(leak)

        self.leaks.append(leak)


# SUGGESTED FIX ENGINE
    

    def _build_fix(self, leak):

        variable = leak["variable"]

        if "returns" in leak["reason"]:

            return {
                "strategy": "context_manager",
                "confidence": "high",
                "summary": (
                    f"Prefer a 'with open(...)' context manager for "
                    f"'{variable}' so the file is automatically closed "
                    f"before returning."
                ),
                "example": (
                    f"with open(<path>, <mode>) as {variable}:\n"
                    f"    # use {variable} here\n"
                    f"    ..."
                ),
                "why": (
                    "The current execution path reaches a return "
                    "while the resource is still live."
                ),
            }

        if "exception" in leak["reason"].lower():

            return {
                "strategy": "finally_or_context_manager",
                "confidence": "high",
                "summary": (
                    f"Ensure '{variable}' is released in a "
                    f"'finally' block, or preferably use a "
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
                    "The resource can remain live when an exception "
                    "leaves the current control-flow path."
                ),
            }

        return {
            "strategy": "explicit_close",
            "confidence": "medium",
            "summary": (
                f"Close '{variable}' after its final use, or use "
                f"a context manager."
            ),
            "example": (
                f"{variable}.close()"
            ),
            "why": (
                "No release operation was detected for this "
                "resource on the analyzed path."
            ),
        }

#HELPERS 
 
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


# REMOVE DUPLICATE FINDINGS


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