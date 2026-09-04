def process(flag):

    f = open("data.txt")

    if flag:
        return f.read()

    f.close()