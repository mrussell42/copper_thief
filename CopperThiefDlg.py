#!/usr/bin/python3
"""Dialog for the Copper Thief KiCad Plugin."""


from wx import ID_ANY, DefaultPosition, Size, DefaultSize, ALL, EXPAND, \
    HORIZONTAL, VERTICAL, Dialog, BoxSizer, StaticText, TextCtrl, \
    CAPTION, CLOSE_BOX, DEFAULT_DIALOG_STYLE, RESIZE_BORDER, \
    Button, ALIGN_CENTER_VERTICAL, ID_OK, \
    ID_CANCEL, ALIGN_RIGHT, BOTH
# import wx.xrc


class CopperThiefDlg(Dialog):

    """Gui for Copper Thief widget."""

    def __init__(self, parent):
        Dialog.__init__(self, parent, id=ID_ANY, title=u"Copper Thief Parameters", pos=DefaultPosition, size=Size(432, 532), style=CAPTION | CLOSE_BOX | DEFAULT_DIALOG_STYLE | RESIZE_BORDER)

        self.SetSizeHints(DefaultSize, DefaultSize)

        bSizer3 = BoxSizer(VERTICAL)

        self.m_comment = StaticText(self, ID_ANY, u"Select a zone to convert to dots\n", DefaultPosition, DefaultSize, 0)
        self.m_comment.Wrap(-1)

        bSizer3.Add(self.m_comment, 0, ALL | EXPAND, 5)

        bSizerSep = BoxSizer(HORIZONTAL)

        self.m_labelSep = StaticText(self, ID_ANY, u"Dot Separation  (mm)  ", DefaultPosition, DefaultSize, 0)
        self.m_labelSep.Wrap(-1)
        self.m_spacing = TextCtrl(self, ID_ANY, u"2", DefaultPosition, DefaultSize, 0)
        self.m_spacing.SetMinSize(Size(1000, -1))

        bSizerSep.Add(self.m_labelSep, 1, ALL | EXPAND, 5)
        bSizerSep.Add(self.m_spacing, 1, ALL, 5)

        bSizer3.Add(bSizerSep, 1, EXPAND, 5)

        ###
        bSizerRad = BoxSizer(HORIZONTAL)

        self.m_labelRad = StaticText(self, ID_ANY, u"Dot Radius  (mm)  ", DefaultPosition, DefaultSize, 0)
        self.m_labelRad.Wrap(-1)
        self.m_radius = TextCtrl(self, ID_ANY, u"0.5", DefaultPosition, DefaultSize, 0)
        self.m_radius.SetMinSize(Size(1000, -1))

        bSizerRad.Add(self.m_labelRad, 1, ALL | EXPAND, 5)
        bSizerRad.Add(self.m_radius, 1, ALL, 5)

        bSizer3.Add(bSizerRad, 1, EXPAND, 5)

        #
        bSizer1 = BoxSizer(HORIZONTAL)

        self.m_buttonGo = Button(self, ID_OK, u"Go", DefaultPosition, DefaultSize, 0)
        self.m_buttonGo.SetDefault()
        bSizer1.Add(self.m_buttonGo, 0, ALL | ALIGN_CENTER_VERTICAL, 5)

        self.m_buttonCancel = Button(self, ID_CANCEL, u"Cancel", DefaultPosition, DefaultSize, 0)
        bSizer1.Add(self.m_buttonCancel, 0, ALL | ALIGN_CENTER_VERTICAL, 5)

        bSizer3.Add(bSizer1, 0, ALIGN_RIGHT | EXPAND, 5)

        self.SetSizer(bSizer3)
        self.Layout()

        self.Centre(BOTH)

    def __del__(self):
        pass
