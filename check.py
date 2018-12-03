file = open(".\\data\\2017.csv")
cmp = open(".\\data\\2017cmp.csv")
file_read = file.readlines()
cmp_read = cmp.readlines()
errors = 0

if len(file_read) != len(cmp_read):
    print("Real Length: " + str(len(file_read)))
    print("Compare Length: " + str(len(cmp_read)))
    errors += 1

if errors == 0:
    if len(file_read) < len(cmp_read):
        length = len(file_read)
    else:
        length = len(cmp_read)

    for i in range(length):
        file_split = file_read[i].split(",")
        cmp_split = cmp_read[i].split(",")
        for j in range(7):
            if file_split[j].strip() != cmp_split[j].strip():
                print("Real Line:    " + file_read[i].strip())
                print("Compare Line: " + cmp_read[i].strip())
                print("Problem in Entry " + str(j).strip())
                errors += 1
else:
    found = False
    index = -1
    while not found:
        index += 1
        file_split = file_read[index].split(",")
        cmp_split = cmp_read[index].split(",")
        for j in range(7):
            if file_split[j].strip().replace("\"", "") != cmp_split[j].strip():
                found = True

    print("Real Line:    " + file_read[index].strip())
    print("Compare Line: " + cmp_read[index].strip())


print("Total Errors = " + str(errors))
