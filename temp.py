def LoadPattern(*filename):
    filename = list(filename)
    with open(filename[0], 'r') as file:
        patterns = file.readlines()
        file.close()
    
    sensitivity = 66.0
    yaw = sensitivity * 0.00101
    
    if 2 > len(filename):
        filename.append(0)

    for i in range(len(patterns)):
        patterns[i] = patterns[i].strip('\n').split(', ')
        patterns[i][0] = round(float(patterns[i][0])/yaw)
        patterns[i][1] = round((float(patterns[i][1])+filename[1])/yaw)
        if i==0:
            patterns[i][1] = 0

    return(patterns)
        
with open('Patterns/DefaultSen.txt', 'r') as pat:
            yPos = float(pat.read())
            pat.close()

print(LoadPattern('Patterns/TheFinals/AKM.txt'))