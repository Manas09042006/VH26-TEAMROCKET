def process(a, b):
    f = open("data.txt")

    if a:
        if b:
            f.close()
            return

        return f.read()

    f.close()
    return