"""
Widgets for pig
"""

from karmapi import pig, base

import curio

import pandas
np = pandas.np

from numpy import random

import math

PI = math.pi

class Circle(pig.PlotImage):


    def compute_data(self):

        r = 50

        self.x = range(-50, 51)

        self.y = [(((r * r) - (x * x)) ** 0.5) for x in self.x]


    def plot(self):

        self.axes.hold(True)
        self.axes.plot(self.x, self.y)

        
        self.axes.plot(self.x, [-1 * y for y in self.y])


class Friday(pig.Video):


    def compute_data(self):

        #self.data = random.randint(0, 100, size=100)
        self.data = list(range(100))

    def plot(self):

        self.axes.plot(self.data)

class MapPoints(pig.PlotImage):

    def compute_data(self):

        self.df = base.load(self.path)

    def plot(self):
        """ See Maps.plot_points_on_map """

        self.df.plot(axes=self.axes)
        
        self.axes.plot(self.data)

        
class InfinitySlalom(pig.Video):

    def compute_data(self):

        #self.data = random.randint(0, 100, size=100)
        self.waves_start = random.randint(5, 10)
        self.waves_end = random.randint(32, 128)
        nwaves = random.randint(self.waves_start, self.waves_end)
        self.x = np.linspace(
            0,
            nwaves,
            512) * PI
        
        self.y = np.sin(self.x / PI) * (64 * PI)

    def plot(self):

        #selector = pig.win_curio_fix()
        #curio.run(self.updater(), selector=selector)
        pass


    async def run(self):
        """ Run the animation 
        
        Loop forever updating the figure

        A little help sleeping from curio
        """
        from karmapi import hush

        # listen
        mick = hush.Connect()

        await mick.frames()
        
        self.axes.hold(True)

        while True:

            data = await mick.get()
            print('infinite data:', len(data))
            
            await curio.sleep(self.interval)

            if random.random() < 0.25:
                print('clearing axes', flush=True)
                self.axes.clear()

            self.compute_data()

            colour = random.random()
            n = len(self.x)
            background = np.ones((n, n))

            background *= colour

            background[0, 0] = 0.0
            background[n-1, n-1] = 1.0
        
            for curve in range(random.randint(3, 12)):


                self.axes.fill(self.x, self.y * 1 * random.random(),
                               alpha=0.3)
                self.axes.fill(self.x, self.y * -1 * random.random(),
                               alpha=0.3)
                self.axes.imshow(background, alpha=0.1, extent=(
                    0, 66 * PI, -100, 100))
                self.draw()
                
                await curio.sleep(1)

class SonoGram(pig.Video):

    def plot(self):
        pass
    
    async def run(self):

        from karmapi import hush

        mic = hush.get_stream()
        
        data = hush.record(mic)

        print(type(data[0]))

        print(data[0][:10])
                  

        ix = 0
        end = None
        offset = 0
        while True:

            zz = hush.decode(data[ix])
            print(len(zz))


            so = []
            for frame in data:
                zz = hush.decode(frame)
                so.append(np.fft.fft(zz))
            
            so = pandas.np.array(so)

            n = so.shape[1]

            #print(max(zz))
            #print(min(zz))
            #print(len(zz[::2]))


            #self.axes.subplot(112)
            #self.axes.clear()
            #self.axes.hold(True)
            #self.axes.plot(zz[0::2])
            #self.axes.subplot(112)
            #self.axes.plot(zz[1::2])
            self.axes.imshow(so.T.real)

            self.draw()
            await curio.sleep(1)

            ix += 1

            if ix >= len(data):
                ix = 0
                

class CurioMonitor:

    def __init__(self):

        import socket

        self.mon = socket.socket()

        host = curio.monitor.MONITOR_HOST
        port = curio.monitor.MONITOR_PORT
        self.mon.connect((host, port))

        self.info = self.mon.recv(10000)

    def ps(self):

        self.mon.send(b'ps\n')
        return self.mon.recv(100000)
                
    def where(self, n):

        self.mon.send('where {}\n'.format(n).encode())
        return self.mon.recv(100000)

class Curio(pig.Docs):
    """ A Curio Monitor 

    ps: show tasks
    where: show where the task is
    cancel: end the task
    """
    def __init__(self, parent=None):
        """ Set up the widget """
        super().__init__(parent)

        self.bindkey(self.dokey)


    def keyPressEvent(self, event):

        print(event)
        #print([x for x in dir(event)])
        key = event.key()
        if key > 256:
            return
        
        key = chr(key)

        self.dokey(key)

    def show_previous(self):

        text, tasks = self.get_tasks()

        max_id = max(tasks)

        while True:
            self.task_id -= 1
            if self.task_id < 0:
                self.task_id = max_id
                
            if self.task_id in tasks:
                text += "\nWhere {}:\n\n".format(self.task_id)
                text += self.mon.where(self.task_id).decode()
                return text
        
        
    def show_next(self):

        text, tasks = self.get_tasks()

        max_id = max(tasks)

        while True:
            self.task_id += 1
            if self.task_id > max_id:
                self.task_id = 0
            if self.task_id in tasks:
                text += "\nWhere {}:\n\n".format(self.task_id)
                text += self.mon.where(self.task_id).decode()
                return text


    def get_tasks(self):

        tasks = set()

        # get set of tasks -- be better to find the
        # curio kernel
        text = self.mon.ps().decode()
        for line in text.split('\n'):
            task = line.split()[0]
            if task.isdigit():
                tasks.add(int(task))

        return text, tasks
        

    def dokey(self, key):

        m = self.mon
        
        text = m.ps().decode()
            
        if key.isdigit():

            ikey = int(key)
            text += "\nWhere {}\n\n".format(ikey)
            text += m.where(ikey).decode()

        elif key == 'J':
            text = self.show_previous()

        elif key == 'K':
            text = self.show_next()
            
        self.set_text(text)


    async def run(self):
        
        
        self.mon = CurioMonitor()
        self.task_id = 0
        self.dokey('P')


        
def get_widget(path):

    parts = path.split('.')

    if len(parts) == 1:
        pig_mod = sys.modules[__name__]
        return base.get_item(path, pig_mod)

    return base.get_item(path)
