def branch_leak():
    f = open("data.txt")

    if condition:
        f.close()
    else:
        return None

    return True