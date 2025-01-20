sensitivity = 50

def LoadPattern(filename):
    yaw = sensitivity * 0.00101
    
    with open(filename, 'r') as file:
        patterns = file.readlines()

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round(float(patterns[i][1])/yaw)

    return(patterns)

print(LoadPattern('Patterns/FCAR.txt'))