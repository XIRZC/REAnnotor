
def threshold(src, dst, th):
    for i in range(len(src)):
        print(abs(src[i]-dst[i]))
        if abs(src[i]-dst[i]) > th:
            return False
    return True

print(threshold([1, 10, 3], [4, 4, 3], 5))