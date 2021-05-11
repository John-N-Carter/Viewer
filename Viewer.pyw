#! python3

from imports import *

poolExecutor = futures.ProcessPoolExecutor(max_workers=1)

'''
    For the given path, get the List of all Images in the directory tree 
'''
def getListOfImages(dirName):
    #~ print(f'Loading {dirName}')
    fileList = []
    with os.scandir(dirName) as it:
        for entry in it:
            if  entry.is_file():
                #~ if imghdr.what(entry.path):
                    #~ fileList.append(entry.path)
                fileList.append(entry.path)
            elif entry.is_dir():
                tmpList = getListOfImages(entry.path)
                fileList.extend(tmpList)
            else: # ignore other things
                pass
                #~ print(f'{entry.name} Should only be a file or directory')
                
    return fileList

class DropImages(wx.FileDropTarget):
    def __init__(self, master):
        self.Master= master
        super().__init__()

    def OnDropFiles(self, x, y, filenames):
        self.Master.DropProcess(filenames)
        return True
        
class PopMenu(wx.Menu): 
    def __init__(self, master): 
        super().__init__() 
        self.Master = master
        self.SetTitle(CONST.APP_NAME)
        #
        self.AppendSeparator()
        #
        self.Item('Random (<ctrl> R)', self.Master.Random)
        self.Item('Stop (<SPACE>)', self.Master.Stop)
        self.Item('Exit (<ESC>)', self.Master.Finish)
    
    def Item(self, name, command):
        menu = wx.MenuItem(self,  wx.ID_ANY, name) # Exit with choice
        self.Append(menu)
        self.Bind(wx.EVT_MENU, command, menu)
        
    
class MyFrame(wx.Frame):
    def __init__(self, root, title):
        super().__init__(None, title = title, pos = (0, 0), style = wx.BORDER_NONE | wx.MAXIMIZE)
        global ExitFlag
        ExitFlag = False
        self.Root = root
        self.Master = self # master used in external clases
        self.Result = None
        self.fileList = []
        self.displayRandom = True
        self.frameSize = self.GetSize()
        self.fileName = None
        #
        self.DC = wx.WindowDC(self)
        self.DC.SetBackground(wx.Brush('black'))
        self.DC.Clear()
        #
        self.config = configparser.ConfigParser()
        #
        self.setup()
        self.ContextData = lambda a, x = self : self.Master.ContextMenu(a)
        self.Bind(wx.EVT_CONTEXT_MENU, self.ContextData, self)
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)
        dr = DropImages(self)
        self.SetDropTarget(dr)
        self.Show(True)
        
    def Message(self, msg = 'I have no idea', title= 'Warning'):
            dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_ERROR)
            ret = dlg.ShowModal()
            
    def ErrorMessage(self, msg = 'Did you seee thr blue screen', title= 'Error'):
            dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.CANCEL | wx.ICON_ERROR)
            ret = dlg.ShowModal()
            
    def WarningMessage(self, msg = 'I have no idea what the relevance is', title= 'Warning'):
            dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_WARNING  | wx.CANCEL)
            ret = dlg.ShowModal()
            
    def InfoMessage(self, msg = 'Something you should no', title= 'Information', timeout = None): # needs timeout!
            dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.CANCEL | wx.ICON_INFORMATION)
            ret = dlg.ShowModal()
            
    def ContextMenu(self, *a):
        self.popmenu = PopMenu(self)
        self.PopupMenu(self.popmenu)
        
    def onKeyPress(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_SPACE:
            self.Stop(event)
        elif keycode == wx.WXK_ESCAPE:
            self.Finish(event)
        elif keycode == wx.WXK_CONTROL_R:
            self.Random(event)
        else:
            pass
        print('Keycode', keycode)

            
    def setup(self): 
        name = os.path.join(CONST.FULL_INI_PATH, CONST.INI_FILE)
        fp = open(name, 'r')
        self.config.read_file(fp)
        fp.close()
        try:
            labels = self.config.sections()
        except:
            self.ErrorMessage('Read failed', 'Access config file.')
            sys.exit()
        fileName = os.path.join(r'H:\Computers\PythonTools\Viewer', 'black.jpg')
        self.fileList = [fileName]
        self.ImageCount = 0
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer)
        self.LastPicture = None
        self.timer.Start(1)    # 1 milli-second interval

    def DropProcess(self, filenames):
        self.fileList = []
        #~ poolExecutor.submit(self.doAsThread, filenames)
        self.doAsThread(filenames)
        self.ImageCount = 0
        if not self.timer.IsRunning():
            self.timer.Start(10)
            
    def doAsThread(self, filenames): # should search as thread and not block
        #~ print(f'Display {len(filenames)}')
        for i, f in enumerate(filenames):
            if os.path.isdir(f):
                tmpList = getListOfImages(f)
                self.fileList.extend(tmpList)
            else:
                self.fileList.append(f)
                #~ if imghdr.what(f):
                    #~ self.fileList.append(f)
                    #~ print(f'Append {f}')
                #~ else:
                    #~ print(f'{f} is not an image')
        #~ if not self.fileList:
            #~ self.WarningMessage(msg = 'Nothing Valid was Dropped', title = 'Drag & Drop Warning')
        

    def LoadImage(self, name): # check its a file/ image and not a dir
        #~ print(f'Load {name}')
        wx.Log.EnableLogging(False) # beter protection needed
        image = wx.Image(name)
        wx.Log.EnableLogging(True)
        #~ print(f'image is {image}')
        try:
            isize = image.GetSize() # this checks if valid image
        except:
            return None, None
        scaleCondition = (isize[0] >= self.frameSize[0]) or (isize[1] >= self.frameSize[1])
        if scaleCondition:
            i = image.GetSize()
            alpha = self.frameSize[0]/i[0]
            beta  = self.frameSize[1]/i[1]
            gamma = min(alpha, beta)
            xs = (int(i[0] * gamma), int(i[1] * gamma))
            image = image.Scale(xs[0], xs[1])
            isize = image.GetSize()
        bitmap = image.ConvertToBitmap()
        return bitmap, isize
        
    def OnTimer(self, a):
        try:
            #
            if self.displayRandom:
                self.ImageCount = r.randrange(len(self.fileList))
                self.fileName = self.fileList[self.ImageCount]
            else:
                if self.ImageCount >= len(self.fileList):
                    self.ImageCount = 0
                self.fileName = self.fileList[self.ImageCount]
                self.ImageCount += 1
            #
        except:
            #~ print('clear because little else too do')
            #~ self.DC.Clear()
            return
        #check is image here, make another choice'
        #~ print(F'Filename: {self.fileName}')
        print(self.ImageCount, self.fileName, self.displayRandom)
        self.bm, self.imageSize = self.LoadImage(self.fileName)
        if self.bm is not None:
            sx = (self.frameSize[0] - self.imageSize[0]) // 2
            sy = (self.frameSize[1] - self.imageSize[1]) // 2
            if self.LastPicture != self.fileName:
                self.DC.Clear()
            self.DC.DrawBitmap(self.bm, sx, sy, True)
            self.LastPicture = self.fileName
        self.timer.Start(1000)
        
    def Random(self, a):
        print('Chose random File')
        self.displayRandom = not self.displayRandom
        if not self.displayRandom:
            try:
                self.ImageCount = self.fileList.index(self.fileName)
            except:
                self.ImageCount = 0

    def Stop(self, a):
        self.timer.Stop()
        self.DC.Clear()
        
    def Finish(self, a):
        self.timer.Stop()
        self.Close()

def gogui():
    version = '(Ver 1.5)'
    title=F'Viewer {version}'
    wx.InitAllImageHandlers()
    app = wx.App()
    frm = MyFrame(app, title)
    frm.Layout()
    frm.Show()
    app.MainLoop()
    
if __name__ == '__main__':
    gogui()





