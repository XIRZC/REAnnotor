import numpy as np
import cv2
# def get_mask_by_point(data, i, j):
#     def dfs(data, fill, point, i, j):
#         # leaf
#         if not np.array_equal(data[i, j, :], point):
#             return
#         fill[i, j, :] = point
#         visited[i][j] = True
#         # adajecent nodes traverse
#         for k in range(4):
#             ni, nj = i + di[k], j + dj[k]
#             print(ni, nj)
#             if boundary((ni, nj), 0, 0, 6, 10) and not visited[ni][nj]:
#                 dfs(data, fill, point, ni, nj)
#     fill = np.zeros_like(data)
#     point = data[i, j, :]
#     di, dj = [1, 0, -1, 0], [0, 1, 0, -1]  # adajecent nodes: down, right, up, left
#     visited = []
#     for a in range(6):
#         visited.append([])
#         for _ in range(10):
#             visited[a].append(False) 
#     dfs(data, fill, point, i, j)
#     print(visited)
#     cv2.imwrite('seg_data.jpg', data)
#     cv2.imwrite('fill.png', fill)
#     return fill
def get_mask_by_point(data, i, j):
    def bfs(data, fill, point, i, j):
        import queue
        q = queue.Queue()
        q.put((i, j))
        fill[i, j] = point
        while not q.empty():
            i, j = q.get()
            for k in range(4):
                ni, nj = i + di[k], j + dj[k]
                if boundary((ni, nj), 0, 0, 6, 10) and np.array_equal(data[ni, nj], point):
                    if np.array_equal(fill[ni, nj], np.zeros(3)):
                        fill[ni, nj] = point
                        q.put((ni, nj))
    def dfs(data, fill, point, i, j):
        fill[i, j] = point

        # adajecent nodes traverse
        for k in range(4):
            ni, nj = i + di[k], j + dj[k]
            if boundary((ni, nj), 0, 0, 6, 10) and np.array_equal(data[ni, nj], point):
                if np.array_equal(fill[ni, nj], np.zeros(3)):
                    dfs(data, fill, point, ni, nj)
    fill = np.zeros_like(data)
    point = data[i, j]
    di, dj = [1, 0, -1, 0], [0, 1, 0, -1]  # adajecent nodes: down, right, up, left
    bfs(data, fill, point, i, j)
    cv2.imwrite('seg_data.jpg', data)
    cv2.imwrite('fill.png', fill)
    return fill

def boundary(p, ltx, lty, rbx, rby):
    if (p[0] >= ltx and p[0] < rbx) and (p[1] >= lty and p[1] < rby):
        return True
    return False

a = [ 
    [ [171, 2, 3],  [0, 0, 0],  [0, 0, 0],   [0, 0, 0],   [0, 0, 0],   [0, 0, 0],   [255, 255, 255], [0, 0, 0],   [0, 0, 0],   [171, 2, 3]],
    [ [171, 2, 3], [171, 2, 3], [171, 2, 3], [171, 2, 3], [0, 0, 0],   [0, 0, 0],   [255, 255, 255], [255, 255, 255], [171, 2, 3], [171, 2, 3]],
    [ [0, 0, 0],   [171, 2, 3], [171, 2, 3], [171, 2, 3], [171, 2, 3], [0, 0, 0],   [255, 255, 255], [255, 255, 255], [0, 0, 0],   [0, 0, 0]],
    [ [171, 2, 3], [171, 2, 3], [171, 2, 3], [0, 0, 0],   [171, 2, 3], [255, 255, 255], [255, 255, 255], [255, 255, 255], [0, 0, 0],   [0, 0, 0]],
    [ [171, 2, 3], [171, 2, 3], [0, 0, 0],   [255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255], [0, 0, 0],   [0, 0, 0],   [0, 0, 0]],
    [ [171, 2, 3], [171, 2, 3], [171, 2, 3], [171, 2, 3], [255, 255, 255], [255, 255, 255], [255, 255, 255], [255, 255, 255], [0, 0, 0],   [0, 0, 0]]
]

arr = np.array(a)
print(arr.shape)
fill = get_mask_by_point(arr, 0, 6)
print(fill)