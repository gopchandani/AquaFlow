import random


def fisher_yates(arr):

    for i in xrange(len(arr)-1, 1, -1):
        j = random.randint(0, i)

        temp = arr[j]
        arr[j] = arr[i]
        arr[i] = temp

    return arr


arr = [1, 2, 3, 4, 5]

print(fisher_yates(arr))
print(fisher_yates(arr))
