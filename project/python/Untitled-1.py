with open('F:\\term6\\data_network\\project\\python\\cache.txt', 'r') as f:
    #lines = f.readlines()
    # Each element in 'lines' is a string ending with '\n' (unless it's the last line without a newline)
    for line in f:
        y = line.split()
        print(y)
    #lines = {line.strip() for line in f if line.strip()}
#print(lines[0])