def process(flag):
    f = open("data.txt")

    if flag:
        f.close()
        return

    return f.read()