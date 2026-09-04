import ast


RESOURCE_CREATORS = {
    "open",
}


RESOURCE_RELEASERS = {
    "close",
}


def is_resource_creator(node):
    
# Check whether an AST Call node creates a resource.
    

    if not isinstance(node, ast.Call):
        return False

    if isinstance(node.func, ast.Name):

        return node.func.id in RESOURCE_CREATORS

    return False


def is_resource_releaser(node):
    
# Check whether an AST Call node releases a resource.
    

    if not isinstance(node, ast.Call):
        return False

    if isinstance(node.func, ast.Attribute):

        return node.func.attr in RESOURCE_RELEASERS

    return False