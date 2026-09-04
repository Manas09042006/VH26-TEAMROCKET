import ast

from analyzer.resource import Resource
from analyzer.detector import (
    is_resource_creator,
    is_resource_releaser,
)


class FlowAnalyzer:


    def __init__(self):
        self.leaks = []

    def analyze(self, tree):
        
        self.leaks = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self.analyze_function(node)

        return self.leaks

    def analyze_function(self, function_node):
        

        resources = {}

        for node in ast.walk(function_node):


# it Detect f = open(...) function in the code
            if isinstance(node, ast.Assign):

                if is_resource_creator(node.value):

                    for target in node.targets:

                        if isinstance(target, ast.Name):

                            resource = Resource(
                                variable=target.id,
                                resource_type="file",
                                open_line=node.lineno,
                            )

                            resources[target.id] = resource

# it Detect the f.close() in the code  
            elif isinstance(node, ast.Expr):

                if is_resource_releaser(node.value):

                    call = node.value

                    if isinstance(call.func, ast.Attribute):

                        variable = call.func.value

                        if isinstance(variable, ast.Name):

                            variable_name = variable.id

                            if variable_name in resources:
                                resources[variable_name].close()

# Find resources still open or not 


        for resource in resources.values():

            if not resource.closed:

                self.leaks.append(
                    {
                        "variable": resource.variable,
                        "resource_type": resource.resource_type,
                        "open_line": resource.open_line,
                        "leak_line": function_node.end_lineno,
                        "reason": "Resource was opened but never closed.",
                    }
                )