import numpy as np
import pandas as pd
import sys

# generate random angle
# then project the angle with random length from 0 to radius


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __str__(self):
        return str((self.x, self.y))


class Circle:
    def __init__(self, origin, radius):
        self.origin = origin
        self.radius = radius


origin = Point(0, 0)
radius = 1000
circle = Circle(origin, radius)
N_MTCD = int(sys.argv[1])

df = pd.DataFrame(columns=['x', 'y'])

for i in range(0, N_MTCD):
    p = np.random.random() * 2 * np.pi
    r = circle.radius * np.sqrt(np.random.random())
    x = round(np.cos(p) * r, 3)
    y = round(np.sin(p) * r, 3)
    df = df.append({'x': x, 'y': y}, ignore_index=True)
    print(i)

df.index.name = 'MTCD_id'
df.to_csv(f'MTCD_position_{N_MTCD}.csv')
