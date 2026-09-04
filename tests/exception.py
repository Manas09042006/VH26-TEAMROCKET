def process():

    f = open("data.txt")

    try:
        risky_operation()
    finally:
        f.close()