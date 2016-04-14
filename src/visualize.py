import networkx as nx
import matplotlib.cbook as cb
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.animation import FuncAnimation, FFMpegWriter
import random
import pg8000
import math
import matplotlib

def distance(a,b):
    return math.sqrt( (a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1]) )

class MyAnimation():
    def __init__(self):
        self.ticks_in_week = 10
        self.tick = 0
        self.current_date = 0
        self.real_sizes = None
        self.nodes = self.get_graph_nodes()
        self.nodesizes = self.get_node_sizes()
        self.dates = self.get_dates()
        self.edges = self.get_edges()
        self.iters = (len(self.dates)-1)*self.ticks_in_week - 2
        self.curr_edges = self.recalc_edges()
        self.sizes = self.nodesizes[self.dates[self.current_date]]
        self.size_inc = self.calc_size_inc()
        self.g = nx.Graph()
        self.g.add_nodes_from(self.nodes)
        self.fig = plt.figure(figsize=(16,9),dpi=240)
        #self.pos = nx.spring_layout(self.g)
        self.load_positions()
        self.resize_pos()
        self.colors = [random.random() for _ in self.nodes]
        self.glow_iter = 20

    def resize_pos(self):
        minx, miny, maxx, maxy = 100, 100, -100, -100
        for node in self.pos:
            minx = min(minx, self.pos[node][0])
            miny = min(miny, self.pos[node][1])
            maxx = max(maxx, self.pos[node][0])
            maxy = max(maxy, self.pos[node][1])
        for node in self.pos:
            self.pos[node][0] = 0.05 + 0.9 * (self.pos[node][0] - minx) / (maxx - minx)
            self.pos[node][1] = 0.05 + 0.85 * (self.pos[node][1] - miny) / (maxy - miny)
        return

    def calc_size_inc(self):
        dt = self.current_date
        currsize = self.nodesizes[self.dates[dt]]
        nextsize = self.nodesizes[self.dates[dt+1]]
        inc = dict()
        for nodeid in currsize:
            inc[nodeid] = float(nextsize[nodeid] - currsize[nodeid]) / self.ticks_in_week
        return inc

    def inc_sizes(self):
        for nodeid in self.sizes:
            self.sizes[nodeid] += self.size_inc[nodeid]
        return

    def draw_glowing_nodes(self, size):
        for i in range(self.glow_iter):
            glowsize = [ x + (6.0 * x * (i + 1) / self.glow_iter) for x in size]
            nx.draw_networkx_nodes(self.g, self.pos, alpha=0.025, cmap='gist_rainbow',
                                   node_color=self.colors, node_size=glowsize, linewidths=0)
        nx.draw_networkx_nodes(self.g, self.pos, alpha=1.0, cmap='gist_rainbow',
                               node_color=self.colors, node_size=size, linewidths=0)
        return

    def get_graph_nodes(self):
        conn = pg8000.connect(user="postgres", password="changeme", database="github")
        cursor = conn.cursor()
        cursor.execute("select id, repo from repos")
        nodelist = cursor.fetchall()
        nodes = dict()
        for el in nodelist:
            nodes[el[0]] = el[1].split('/')[1]
        cursor.close()
        conn.close()
        return nodes

    def get_node_sizes(self):
        conn = pg8000.connect(user="postgres", password="changeme", database="github")
        cursor = conn.cursor()
        cursor.execute("select week, repo_id, size from repo_changes")
        changes = cursor.fetchall()
        nodesizes = dict()
        for el in changes:
            if not el[0] in nodesizes:
                nodesizes[el[0]] = dict()
            nodesizes[el[0]][el[1]] = el[2]
        cursor.close()
        conn.close()
        return nodesizes

    def get_dates(self):
        conn = pg8000.connect(user="postgres", password="changeme", database="github")
        cursor = conn.cursor()
        cursor.execute("select dt from all_weeks order by dt")
        dates = cursor.fetchall()
        dates = [d[0] for d in dates]
        cursor.close()
        conn.close()
        return dates

    def get_edges(self):
        conn = pg8000.connect(user="postgres", password="changeme", database="github")
        cursor = conn.cursor()
        cursor.execute("select week, first_id, second_id from edges")
        alledges = cursor.fetchall()
        edges = dict()
        for edge in alledges:
            if not edge[0] in edges:
                edges[edge[0]] = []
            edges[edge[0]].append([edge[1],edge[2]])
        cursor.close()
        conn.close()
        return edges

    def move_node(self, mynode, edges):
        xd, yd = 0.0, 0.0
        node_dist = [ [distance(self.pos[mynode], self.pos[node]), node] for node in self.nodes if node <> mynode and self.sizes[node] > 0.0]
        node_dist = sorted(node_dist)
        for noded in node_dist:
            dist = noded[0]
            node = noded[1]
            dx = self.pos[mynode][0] - self.pos[node][0]
            dy = self.pos[mynode][1] - self.pos[node][1]
            if edges is not None and node in edges:
                if dist > 0.1:
                    xd -= dx*((dist-0.1)/100.0)
                    yd -= dy*((dist-0.1)/100.0)
            if dist < 0.15:
                l = math.sqrt(dx*dx + dy*dy)
                if l > 0:
                    dx /= l
                    dy /= l
                else:
                    dx = (random.random() - 0.5) / 10.
                    dy = (random.random() - 0.5) / 10.
                xd += dx*((0.2-dist)*(0.2-dist) / 10.0)
                yd += dy*((0.2-dist)*(0.2-dist) / 10.0)
        self.pos[mynode][0] += xd
        self.pos[mynode][1] += yd
        self.pos[mynode][0] = min(0.95, max(0.05, self.pos[mynode][0]))
        self.pos[mynode][1] = min(0.9, max(0.05, self.pos[mynode][1]))
        return

    def recalc_edges(self):
        edges = dict()
        for edge in self.edges[self.dates[self.current_date]]:
            if not edge[0] in edges:
                edges[edge[0]] = set()
            edges[edge[0]].add(edge[1])
            if not edge[1] in edges:
                edges[edge[1]] = set()
            edges[edge[1]].add(edge[0])
        return edges

    def recalc_node_positions(self):
        for node in self.nodes:
            if self.sizes[node] > 0.0:
                self.move_node(node, self.curr_edges.get(node))
        return

    def draw_timeline(self):
        plt.axhspan(0.97, 0.98, 0.1, 0.9, facecolor='#808080', linewidth=0)
        for year in range(2006, 2017):
            plt.text(0.1 + 0.75*(year-2006)/10.0, 0.96,
                     "%d" % year,
                     size = 10,
                     weight='bold',
                     color='white',
                     horizontalalignment='left',
                     verticalalignment='top',
                     transform=plt.gca().transAxes)
        cur = self.current_date * self.ticks_in_week + self.tick
        top = len(self.dates) * self.ticks_in_week
        pos = 0.1 + 0.8 * (float(cur) / float(top))
        plt.axvline(pos, 0.963, 0.987, color='orange', linewidth=3)
        plt.text(0.95, 0.01, "http://0x0fff.com",
                 size=8,
                 weight='bold',
                 style='italic',
                 color='white',
                 horizontalalignment='center',
                 transform=plt.gca().transAxes)
        return

    def update_animation(self, i):
        print "Frame %d / %d" % (i, self.iters)
        self.recalc_node_positions()
        plt.clf()
        ax = plt.Axes(self.fig, [0., 0., 1., 1.])
        ax.autoscale(False)
        ax.set_axis_bgcolor('#141414')
        self.fig.add_axes(ax)
        self.g.remove_edges_from(self.g.edges())
        self.g.add_edges_from(self.edges[self.dates[self.current_date]])
        nx.draw_networkx_edges(self.g, self.pos, edge_color='#2F2F2F')
        self.real_sizes = [2000.0 * self.sizes[node] for node in self.g.nodes()]
        self.draw_glowing_nodes(self.real_sizes)
        self.draw_labels(self.g, self.pos, sizes=self.real_sizes, labels=self.nodes)
        self.tick += 1
        self.inc_sizes()
        if self.tick >= self.ticks_in_week:
            self.current_date += 1
            if self.current_date == len(self.dates):
                self.current_date -= 1
            self.tick = 0
            self.curr_edges = self.recalc_edges()
            self.sizes = self.nodesizes[self.dates[self.current_date]]
            self.size_inc = self.calc_size_inc()
        #if i == self.iters - 1:
        #    self.save_positions()
        self.draw_timeline()
        return

    def draw_labels(self, G, pos,
                    sizes=None,
                    labels=None,
                    font_family='sans-serif'):
        ax = plt.gca()
        i = 0
        for n, label in labels.items():
            (x, y) = pos[n]
            y += 0.015 + 0.03 * math.sqrt(sizes[i])/3.14/10.0
            if not cb.is_string_like(label):
                label = str(label)  # this will cause "1" and 1 to be labeled the same
            font_size = 8
            font_color = 'white'
            font_weight = 'normal'
            if sizes[i] > 50:
                font_size = 12
                font_weight = 'semibold'
            if sizes[i] > 120:
                font_color = 'yellow'
            if sizes[i] > 10:
                t = ax.text(x, y,
                          label,
                          size = font_size,
                          color = font_color,
                          family = font_family,
                          weight = font_weight,
                          style = 'italic',
                          horizontalalignment = 'center',
                          verticalalignment = 'center',
                          transform=ax.transData,
                          clip_on=True,
                          )
            i += 1
        return

    def load_positions(self):
        f = open('/projects/personal/positions.csv', 'rb')
        self.pos = dict()
        for line in f:
            node, x, y = line.strip().split('|')
            self.pos[int(node)] = [float(x), float(y)]
        f.close()
        return

    def save_positions(self):
        f = open('/projects/personal/positions.csv', 'wb')
        for node in self.pos:
            f.write("%d|%f|%f\n" % (node, self.pos[node][0], self.pos[node][1]))
        f.close()
        return

    def run(self):
        anim = FuncAnimation(self.fig, self.update_animation,repeat=False,frames=(len(self.dates)-1)*self.ticks_in_week - 2,
                             interval=10, blit=False)
        #self.save_positions()
        #plt.savefig('/projects/personal/1.png', dpi = 80)
        plt.show()

    def writevideo(self):
        #print animation.writers.list()
        #matplotlib.rcParams['animation.ffmpeg_args'] = ['-report', '/tmp/ffmpeg.log']
        #FFMpegWriter = animation.writers['ffmpeg']
        metadata = dict(title='Github Data Projects', artist='0x0FFF',
                        comment='Evolution of open source data projects')
        writer = FFMpegWriter(fps=30,
                              bitrate=8000,
                              metadata=metadata
                             )
        i = 0
        #self.iters = 200
        with writer.saving(self.fig, "/projects/personal/writer_test.mp4", 120):
            while i < self.iters:
                self.update_animation(i)
                writer.grab_frame()
                i += 1
        return

m = MyAnimation()
m.writevideo()
#m.run()