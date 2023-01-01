import numpy as np
from numba import njit
y = 2
x = 6
arr = np.zeros((y, x))
arr[1][2] = 1
arr[1][2] = 1

@njit
def doubler(array):
    size = array.shape
    new_arr_shape = (size[0] * 2, size[1] * 2)
    new_arr = np.zeros(new_arr_shape)
    for y_index, y_ele in enumerate(new_arr):
        for x_index, x_ele in enumerate(y_ele):
            new_arr[y_index][x_index] = array[y_index // 2][x_index // 2]
    return new_arr


arr = doubler(arr)
arr = doubler(arr)
arr = doubler(arr)
arr = doubler(arr)
arr = doubler(arr)
arr = doubler(arr)
print(arr.shape)

