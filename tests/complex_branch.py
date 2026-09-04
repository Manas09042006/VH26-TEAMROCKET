def process(flag):
    input_file = open("input.txt")
    output_file = open("output.txt")

    if flag:
        input_file.close()
        output_file.close()
        return

    input_file.close()

    return output_file.read()