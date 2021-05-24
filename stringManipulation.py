def stringFormat(input, total):
    outString = ""

    if input == "all":
        for i in range(1, total + 1):
            if i == max(range(1, total + 1)):
                outString += "{}".format(i)
            else:
                outString += "{},".format(i)
        return outString

    counterparts = input.split(",")

    for index, part in enumerate(counterparts):
        if "-" in part:
            minimum = int(part.split("-")[0])
            maximum = int(part.split("-")[1]) + 1
            for i in range(minimum, maximum):
                if i == max(range(minimum, maximum)) and index == len(counterparts) - 1:
                    outString += "{}".format(i)
                else:
                    outString += "{},".format(i)

        else:
            if index == len(counterparts) - 1:
                outString += "{}".format(part)
            else:
                outString += "{},".format(part)

    return outString
