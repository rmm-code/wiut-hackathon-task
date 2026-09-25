import math
import cv2
import numpy as np


def inside(point, polygon):
    return (
        bool(polygon)
        and cv2.pointPolygonTest(
            np.asarray(polygon, np.float32), tuple(map(float, point)), False
        )
        >= 0
    )


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def cosine(a, b):
    return dot(a, b) / max(1e-9, math.hypot(*a) * math.hypot(*b))


def line_side(point, line):
    a, b = line
    return (b[0] - a[0]) * (point[1] - a[1]) - (b[1] - a[1]) * (point[0] - a[0])


def crossed(a, b, line):
    return (
        line_side(a, line) * line_side(b, line) < 0
        and line_side(line[0], [a, b]) * line_side(line[1], [a, b]) <= 0
    )


def iou(a, b):
    width = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    height = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    intersection = width * height
    area = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1])
    return intersection / max(area - intersection, 1e-9)
