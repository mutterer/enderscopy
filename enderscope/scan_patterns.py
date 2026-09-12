"""Scan-path generation and preview plotting for multi-position acquisitions."""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


class ScanPatterns:
    """
    A class to generate (and plot) scan patterns for the stage

    The patterns are generated as numpy arrays
    """

    def plot_path(path = np.array([[0,0]]), labels=True, field = (10,10), title='Path preview'):
        x=path[:, 0]
        y=path[:, 1]
        field = Rectangle((0,0),field[0],field[1])
        rectangle = Rectangle((0,0), 200, 190,
                          edgecolor='green', facecolor='#00ff0010', linewidth=1)
        plt.gca().add_patch(rectangle)
        plt.plot(x,y, marker='x')
        plt.axis('equal')
        ticks = np.arange(-50, 221, 25)
        plt.xticks(ticks)
        plt.yticks(ticks)
        plt.grid(linestyle='--', linewidth=0.7, alpha=0.7)
        plt.xlim(-10, 200)
        plt.ylim(-10, 200)
        plt.xlabel('x axis')
        plt.ylabel('y axis')
        plt.title(title)
        if labels:
            for idx, (x_pos, y_pos) in enumerate(zip(x, y)):
                plt.text(x_pos, y_pos, str(idx+1), fontsize=10, color='gray', ha='right', va='bottom')
                f = Rectangle((x_pos-field.get_width()/2,y_pos-field.get_height()/2),
                              field.get_width(), field.get_height(),
                              edgecolor='red', facecolor='none', linewidth=0.25
                             )
                plt.gca().add_patch(f)

    def raster(cols=4, rows=3):
        return np.array(list((x,y) for y in range(rows) for x in range(cols)))

    def snake(cols=4, rows=3):
        return np.array(
            list((x,y)
                 for y in range(rows)
                 for x in range((cols-1)*(y%2),cols-(cols+1)*(y%2),((y+1)%2)-1*((y%2)))
                ))

    def random(num_points = 10, seed=1):
        x_min, x_max = 0, 180  # Range for x values
        y_min, y_max = 0, 180  # Range for y values
        np.random.seed(seed)
        return np.column_stack((
            np.random.uniform(x_min, x_max, num_points),
            np.random.uniform(y_min, y_max, num_points)))

    def spiral(num_points = 50):
        directions = np.array([[1,0],[0,1],[-1,0],[0,-1]])
        d = 0
        i = 1
        p = np.array([0,0])
        sp = np.array([p])
        while len(sp)<num_points:
            for j in range(i):
                p=p+directions[d]
                sp = np.append(sp,[p], axis=0)
            d = (d+1)%4
            i = i + (d%2==0)
        return np.array(sp[:num_points])
