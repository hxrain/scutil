# -*- coding: utf-8 -*-

import math

import numpy as np


def distance(usrdat, a, b):
    # 默认的距离计算函数,使用欧氏距离
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


_sqrt_2pi = math.sqrt(2 * math.pi)


def gaussian_kernel(distance, bandwidth):
    # 默认的核函数,使用高斯核函数
    a = 1 / (bandwidth * _sqrt_2pi)
    b = (distance / bandwidth) ** 2
    return a * math.exp(-0.5 * b)


class MeanShift(object):
    # MeanShift目标核数量自适应分类功能类
    def __init__(self, distance_fn=distance, kernel_fn=gaussian_kernel):
        self.kernel = kernel_fn  # 核函数
        self.distance_fn = distance_fn  # 距离计算函数
        self.bandwidth = 0.5  # 默认核带宽
        self.STOP_THRESHOLD = 1e-4  # 迭代停止的限定阈值(新核与其样本值的距离最大值小于此阈值时计算停止)
        self.CLUSTER_THRESHOLD = 1e-4  # 新核与样本的距离小于此阈值,则样本归属此新核
        self.max_loops = 100000  # 最大循环次数,避免离散的样本与参数不符进入死循环
        self.usrdat = None  # 调用距离函数时使用

    def fit(self, points):

        shift_points = points.copy()
        shifting = [True] * len(points)

        for loop in range(self.max_loops):
            max_dist = 0
            for i in range(0, len(shift_points)):
                if not shifting[i]:
                    continue
                p_shift_init = shift_points[i].copy()
                shift_points[i] = self._shift_point(shift_points[i], points, self.bandwidth)
                dist = self.distance_fn(self.usrdat,shift_points[i], p_shift_init)
                max_dist = max(max_dist, dist)
                shifting[i] = dist > self.STOP_THRESHOLD

            if (max_dist < self.STOP_THRESHOLD):
                break
        cluster_ids = self._cluster_points(shift_points)
        return shift_points, cluster_ids

    def _shift_point(self, point, points, kernel_bandwidth):
        shift_x = 0.0
        shift_y = 0.0
        scale = 0.0
        for p in points:
            dist = self.distance_fn(self.usrdat,point, p)
            weight = self.kernel(dist, kernel_bandwidth)
            shift_x += p[0] * weight
            shift_y += p[1] * weight
            scale += weight
        shift_x = shift_x / scale
        shift_y = shift_y / scale
        return [shift_x, shift_y]

    def _cluster_points(self, points):
        cluster_ids = []
        cluster_idx = 0
        cluster_centers = []

        for i, point in enumerate(points):
            if (len(cluster_ids) == 0):
                cluster_ids.append(cluster_idx)
                cluster_centers.append(point)
                cluster_idx += 1
            else:
                for center in cluster_centers:
                    dist = self.distance_fn(self.usrdat,point, center)
                    if (dist < self.CLUSTER_THRESHOLD):
                        cluster_ids.append(cluster_centers.index(center))
                if (len(cluster_ids) < i + 1):
                    cluster_ids.append(cluster_idx)
                    cluster_centers.append(point)
                    cluster_idx += 1
        return cluster_ids


if __name__ == '__main__':
    from sklearn.datasets.samples_generator import make_blobs
    import matplotlib.pyplot as plt
    import random


    def colors(n):
        ret = []
        for i in range(n):
            ret.append((random.uniform(0, 1), random.uniform(0, 1), random.uniform(0, 1)))
        return ret


    def main():
        centers = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        X0, _ = make_blobs(n_samples=300, centers=centers, cluster_std=0.4)
        X = [[X0[i][0], X0[i][1]] for i in range(X0.shape[0])]
        X[0][0] = 0
        X[0][1] = 0
        mean_shifter = MeanShift()
        _, mean_shift_result = mean_shifter.fit(X, kernel_bandwidth=0.5)

        np.set_printoptions(precision=3)
        print('input: {}'.format(X))
        print('assined clusters: {}'.format(mean_shift_result))
        color = colors(np.unique(mean_shift_result).size)

        for i in range(len(mean_shift_result)):
            plt.scatter(X0[i, 0], X0[i, 1], color=color[mean_shift_result[i]])
        plt.show()


    main()
