#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.9.9pre on Fri Jan  3 20:14:00 2020
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class MyFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((400, 300))
        self.SetTitle("frame")
        
        self.panel_1 = wx.Panel(self, wx.ID_ANY)
        
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        self.button_1 = wx.Button(self.panel_1, wx.ID_ANY, "Show Dialog (modal)")
        sizer_1.Add(self.button_1, 0, wx.ALL, 4)
        
        static_text_1 = wx.StaticText(self.panel_1, wx.ID_ANY, "Text from dialog:")
        sizer_1.Add(static_text_1, 0, wx.ALL, 4)
        
        self.text_ctrl_1 = wx.TextCtrl(self.panel_1, wx.ID_ANY, "", style=wx.TE_READONLY)
        sizer_1.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 4)
        
        self.panel_1.SetSizer(sizer_1)
        
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.on_button_show_modal, self.button_1)
        # end wxGlade

    def on_button_show_modal(self, event):  # wxGlade: MyFrame.<event_handler>
        with MyDialog(self) as dlg:
            dlg.text_ctrl_1.SetValue(self.text_ctrl_1.GetValue())
            if dlg.ShowModal() == wx.ID_OK:
                self.text_ctrl_1.SetValue(dlg.text_ctrl_1.GetValue())

# end of class MyFrame

class MyDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MyDialog.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        self.SetTitle("dialog")
        
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        
        static_text_1 = wx.StaticText(self, wx.ID_ANY, "Enter text:")
        sizer_1.Add(static_text_1, 0, wx.ALL, 8)
        
        self.text_ctrl_1 = wx.TextCtrl(self, wx.ID_ANY, "")
        sizer_1.Add(self.text_ctrl_1, 0, wx.ALL | wx.EXPAND, 8)
        
        sizer_1.Add((20, 20), 1, wx.ALIGN_CENTER | wx.EXPAND, 0)
        
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(sizer_2, 0, wx.ALIGN_RIGHT | wx.ALL, 8)
        
        self.button_1 = wx.Button(self, wx.ID_CANCEL, "")
        sizer_2.Add(self.button_1, 0, 0, 0)
        
        self.button_2 = wx.Button(self, wx.ID_OK, "")
        self.button_2.SetDefault()
        sizer_2.Add(self.button_2, 0, 0, 0)
        
        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        
        self.Layout()
        # end wxGlade

# end of class MyDialog

class MyApp(wx.App):
    def OnInit(self):
        self.frame = MyFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
