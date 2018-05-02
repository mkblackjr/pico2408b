import time
import sys

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
from matplotlib.pylab import xlim,ylim

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from threading import Thread
from picoscope2408b import Picoscope2408b
import numpy as np
import matplotlib.pyplot as plt
import sys
import traceback

LARGE_FONT= ("Helvetica", 16)

def center(toplevel):
    toplevel.update_idletasks()
    w = toplevel.winfo_screenwidth()
    h = toplevel.winfo_screenheight()
    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = w/2 - size[0]/2
    y = h/2 - size[1]/2
    toplevel.geometry("%dx%d+%d+%d" % (size + (x, y)))

class PicoscopeGUI(tk.Frame):

    def __init__(self, parent, controller):
        self._run = True
        tk.Frame.__init__(self, parent)
        self.config(bg='black')
        self._picoscope = Picoscope2408b()
        self._mouse_x = 0
        self._mouse_y = 0
        self._labels = {}

        # Run Continuously
        photo = tk.PhotoImage(file="images\\Start_Collection.gif")
        self._img = photo        
        self._runloop_button = tk.Button(self,width=200,image=photo,borderwidth=0,highlightthickness=0,relief="flat",
        state='disabled',command=lambda: self.click_run_loop())
        self._runloop_button.grid(row=7,padx=0, columnspan=3,column=0,rowspan=1,sticky='nsew')
        
        photo = tk.PhotoImage(file="images\\Collect_Block.gif")
        self._img2 = photo
        self._runonce_button = tk.Button(self,state='disabled',image=photo,borderwidth=0,highlightthickness=0,relief="flat",
        command=lambda: self.click_run_once()) 
        self._runonce_button.grid(row=7,columnspan=3,column=3,rowspan=1,sticky='nsew')
       
        photo = tk.PhotoImage(file="images\\Exit.gif")
        self._exit_button = tk.Button(self,state='normal', image=photo,borderwidth=0,highlightthickness=0,relief="flat",
        command=lambda: self.click_exit()) 
        self._exit_button.img = photo
        self._exit_button.grid(row=7,columnspan=2,column=6,rowspan=1,sticky='nsew')
       
        image_frame = tk.Frame(self, height=400, width=300,bg='black')
        image_frame.grid(row=0,rowspan=7,column=5,columnspan=3)
        
        self._image_frame = image_frame
        
        self.set_label("Picoscope","Connecting","yellow")
        self.set_label("Range A","-- m","yellow")
        self.set_label("Range B","-- m","yellow")
        self.set_label("Depolarization Ratio","--","yellow")
        self.set_label("Channel A","Legend","blue")
        self.set_label("Channel B","Legend","orange")
        self.set_label("Channel C","Legend","green")
        
        f = Figure(figsize=(5,5), dpi=100)
        self.a = f.add_subplot(111)
        # self.a.set_adjustable('box-forced')
        self.a.axis('off')
        self.a.autoscale(True)
        f.subplots_adjust(left=0,right=1,bottom=0,top=1)
        data = {'time':np.linspace(0,self._picoscope._sampling_duration,self._picoscope._samples),
                'data':np.array([np.linspace(-1.1,1.1,self._picoscope._samples),
                                 np.linspace(-0.5,0.5,self._picoscope._samples),
                                 np.linspace(-0.5,0.5,self._picoscope._samples),
                                 np.linspace(-1.1,1.1,self._picoscope._samples)]).reshape(self._picoscope._samples,4)}
        # data['data'] /= 40
        self.plot = self.a.plot('time','data',data=data) # timedata is 1D array, data is 2D array
        # self.a.legend()
        # self.plot = self.a.imshow(initial_data,origin='lower')
        
        for p in self.plot:
            p.axes.axis('tight')
        # self.plot.axes.axis('tight')
        self.f = f
        
        canvas = FigureCanvasTkAgg(f, self)#image_frame was previously self
        canvas.draw()
        
        #canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        
        widget = canvas.get_tk_widget()
        widget.config(height=500,width=500)
        widget.grid(row=0,column=0,columnspan=5,rowspan=6)
        #widget.pack()
        self.canvas = canvas
        #toolbar = NavigationToolbar2TkAgg(canvas, self)
        #toolbar.update()
        #canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        
        #fig, ax = plt.subplots()
        #self.canvas.mpl_connect('motion_notify_event', self.motionnotify)
        self.canvas.mpl_connect('button_press_event', self.button_press)
        #self.canvas.mpl_connect('figure_enter_event', self.figure_enter)
        #self.canvas.mpl_connect('figure_leave_event', self.figure_leave)

        t = Thread(target=self.update,args=())
        t.daemon = True
        t.start()
        return

    def set_label(self,name,value,color='white'):
        if name in self._labels.keys():
            self._labels[name].config(text="{}".format(value),fg = color)
        else:
            idx = len(self._labels.keys())
            label_title = tk.Label(self._image_frame,  text="{}:".format(name), font=LARGE_FONT, bg='black', fg='white')
            label_title.grid(row=idx,padx=10,column=0,columnspan=2, sticky='e')
        
            label_value = tk.Label(self._image_frame,  text="{}".format(value), font=LARGE_FONT,bg = 'black', fg=color)
            label_value.grid(row=idx,column=2,columnspan=1)
            self._labels[name] = label_value
        
    def click_exit(self):
        self._picoscope.close()
        sys.exit()
    
    def button_press(self,event):
        return
        x = event.x/500.0*600.0
        y = event.y/500.0*600.0
        self.horiz.set_ydata(y)
        self.vert.set_xdata(x)
        self._crosshair.set_data([x],[y])
        self._mouse_x = event.x
        self._mouse_y = event.y
        
    def figure_enter(self,event):
        self._label_val.grid(row=1,column=1,columnspan=1)
 
    def figure_leave(self,event):
        self._label_val.grid_forget()
    
    def click_run_loop(self):
        self._picoscope.toggle_save()
        
    def click_run_once(self):
        self._picoscope.run_once()
        
    def update(self):
        update_time = time.time()
        # #self._laser = hardware.Laser()
        # #image = Image.open("Start_Laser.png")
        self._picoscope.open()
        # laser_on = self._picoscope.laser_on
        # shutter_open = self._picoscope.shutter_open

        self._picoscope.start()

        start_collection = tk.PhotoImage(file="images\\Start_Collection.gif")
        stop_collection = tk.PhotoImage(file="images\\Stop_Collection.gif")
        
        self._runloop_button.config(state='normal')
        self._runonce_button.config(state='normal')
            
        while(self._run):
            if not self._picoscope._allow_save:
                self._runloop_button.config(image=start_collection)
            else:
                self._runloop_button.config(image=stop_collection) 

            self.set_label("Range A","{} m".format(self._picoscope.rangeA),"green")
            self.set_label("Range B","{} m".format(self._picoscope.rangeB),"green")
            self.set_label("Depolarization Ratio","{}".format(self._picoscope.depolarization_ratio),"green")
            
            if time.time() - update_time > 2: # Only update this every 2 seconds
                update_time = time.time()
                if self._picoscope.ready:
                    self.set_label("Picoscope","Ready","green")
                else:
                    self.set_label("Picoscope","Offline","red")

            try:
                for chan,i in zip(self.plot,range(4)):
                    chan.set_data(self._picoscope.t,self._picoscope.channel_data[i]/max(self._picoscope.channel_data[i]))
                    # xlim(min(self._picoscope.t),max(self._picoscope.t))
                    # ylim(min(self._picoscope.channel_data[i])-1,max(self._picoscope.channel_data[i])+1)
                    # rescale
                # self.plot.set_data(self._picoscope.data) 
                # shape = self._picoscope.image.shape
                # max_w = self._picoscope._camera._settings.roiWidth
                # max_h = self._picoscope._camera._settings.roiHeight
                # x = min(int(self._mouse_x/500.0*max_w),max_w)
                # y =  min(int(self._mouse_y/500.0*max_h),max_h)
                # #self._label_val.config(text = "{}".format(self._picoscope.image[y,x]))
                # self.set_label("Pixel Count","{}".format(self._picoscope.image[y,x]))
                # self.set_label("X,Y","({},{})".format(x,y))
                self.canvas.draw()
            except:
                traceback.print_exc(file=sys.stdout)
                self.destroy()
                break
            time.sleep(.5)
            #self.n += 1
            #data = [[1,2,3,4,5,6,7,8],[5,6,1,self.n,8,9,3,5]]
            #self.plot.set_data(data) 
            #self.canvas.draw()
            #time.sleep(.5)
        

class UI(tk.Tk):    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.config(bg = 'black')
        #tk.Tk.iconbitmap(self, default="clienticon.ico")
        tk.Tk.wm_title(self, "Picoscope")
        
        container = tk.Frame(self,bg='black')
        self.resizable(0,0)
        self.geometry("850x580")
        center(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        for F in (PicoscopeGUI,):
            frame = F(container, self)
            frame.place(in_=container,x=0,y=0,relwidth=1,relheight=1)
            self.frames[F] = frame

        frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(PicoscopeGUI)
    
    
            
    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.lift()
        frame.tkraise()


if __name__ == "__main__":
    
    app = UI()
    app.mainloop()
    """
    sys.exit()
    
    root = tk.Tk()
    button = tk.Button(root,text="Start").grid(row=2,column=2)
    #button.pack()
#    photo=tk.PhotoImage(file="start.jpg")
    
    image = Image.open("start.jpg")
    photo = ImageTk.PhotoImage(image)


    button = tk.Button(root,image=photo,text="end").grid(row=0,column=0)

    #a = TestPlot(root)
    
    root.mainloop()
    
    """