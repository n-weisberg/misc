for i in range(0,9):
    for j in range(0,9):
        for k in range(0,9):
            if (i == 6 or j == 8 or k == 2):
                if (i == 1 or i == 4) or (j == 6 or j == 4) or (k == 6 or k == 1):
                    if (i == 0 or i == 6) or (j == 2 or j == 6) or (k == 2 or k == 0):
                        if (i == 0 or i == 6):
                            match = i
                        if (j == 2 or j == 6):
                            match = j
                        if (k == 2 or k == 0):
                            match = k
                        if ((i == 0 or i == 6) and match != i) or ((j == 2 or j == 6) and match != j) or ((k == 2 or k == 0) and match != k):
                            if (i != 7 and j != 3 and k != 8):
                                if (i == 8 or i == 0) or (j == 3 or j == 0) or (k == 3 or k == 8):
                                    print(i, j, k)