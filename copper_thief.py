#!/usr/bin/python3

import numpy as np
import wx
import pcbnew
import os
import sys
import logging
from . import CopperThiefDlg
THIEVING_ZONENAMES = ['thieving', 'theiving', 'thief', 'theif', 'dotsarray']


def FromMM(x):
    return pcbnew.FromMM(float(x))


class StreamToLogger(object):

    """Fake stream object that redirects writes to a logger instance."""

    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self, *args, **kwargs):
        pass


# set up logger
logging.basicConfig(level=logging.DEBUG,
                    filename="thief.log",
                    filemode='w',
                    format='%(asctime)s %(name)s %(lineno)d:%(message)s',
                    datefmt='%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)
stdout_logger = logging.getLogger('STDOUT')
sl_out = StreamToLogger(stdout_logger, logging.INFO)
sys.stdout = sl_out

stderr_logger = logging.getLogger('STDERR')
sl_err = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl_err


class CopperThief_Dlg(CopperThiefDlg.CopperThiefDlg):
    def SetSizeHints(self, sz1, sz2):
        if wx.__version__ < '4.0':
            self.SetSizeHintsSz(sz1, sz2)
        else:
            super(CopperThief_Dlg, self).SetSizeHints(sz1, sz2)

    def onDeleteClick(self, event):
        return self.EndModal(wx.ID_DELETE)

    def onConnectClick(self, event):
        return self.EndModal(wx.ID_REVERT)

    def __init__(self, parent):
        CopperThiefDlg.CopperThiefDlg.__init__(self, parent)
        self.SetMinSize(self.GetSize())


class Copper_Thief(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Copper Thief"
        self.category = "Modify PCB"
        self.description = "Replace a zone with dots"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), "./dots_icon.png")
        self.show_toolbar_button = True

    def Warn(self, message, caption='Warning!'):
        dlg = wx.MessageDialog(
            None, message, caption, wx.OK | wx.ICON_WARNING)
        dlg.ShowModal()
        dlg.Destroy()

    def Run(self):



        board = pcbnew.GetBoard()
        windows = [x for x in wx.GetTopLevelWindows()]

        try:
            parent_frame = [x for x in windows if 'pcbnew' in x.GetTitle().lower()][0]
        except IndexError:
            # Kicad 6 window title is "pcb editor"
            parent_frame = [x for x in windows if 'pcb editor' in x.GetTitle().lower()][0]
                
        print(parent_frame)
        aParameters = CopperThief_Dlg(parent_frame)

        aParameters.m_spacing.SetValue("2")
        aParameters.m_radius.SetValue("0.5")
        modal_result = aParameters.ShowModal()
        if modal_result == wx.ID_OK:
            spacing = float(aParameters.m_spacing.GetValue())
            radius = float(aParameters.m_radius.GetValue())
            logger.info(f"Spacing {spacing}")
            zones = []
            for z in board.Zones():
                if z.IsSelected():
                    zones.append(z)

            dotter = Dotter()
            for zone in zones:
                zonename = zone.GetZoneName()
                if zonename.lower() in THIEVING_ZONENAMES:
                    dotter.apply_dots(zone, spacing=spacing, radius=radius)
                    board.Remove(zone)
                else:
                    wx.MessageBox("Zone name must be \"theiving\".", "Check zone name.", wx.OK)
        aParameters.Destroy()


class Dotter():

    def __init__(self):
        self.pcb = pcbnew.GetBoard()

    def apply_dots(self, zone, spacing=2, radius=0.5):
        """Iterate over the zone area and add dots if inside the zone."""
        layer = zone.GetLayer()
        bbox = zone.GetBoundingBox()
        zonepolys = zone.GetFilledPolysList(layer)

        # Deflate (ie shrink) the zone so we don't place dots close to the zone edge
        zonepolys.Deflate(FromMM(spacing / 2), 16)
        print(f"Box Corners {bbox.GetLeft()/ 1e6}, {bbox.GetRight() / 1e6}")
        for x in np.arange(bbox.GetLeft() / 1e6, bbox.GetRight() / 1e6, spacing):
            for y in np.arange(bbox.GetTop() / 1e6, bbox.GetBottom() / 1e6, spacing):
                if zonepolys.Collide(pcbnew.VECTOR2I(FromMM(x), FromMM(y)), FromMM(0.5)):
                    dot = self.create_dot(layer, x, y, radius, 1)
                    self.pcb.Add(dot)
        pcbnew.Refresh()
        # self.RefillBoardAreas()

    def create_dot(self, layer, x, y, r, width):
        """Create a dot."""
        print(f"Creating dot at {x}, {y} with radius {r}")

        center = pcbnew.wxPoint(FromMM(x), FromMM(y))
        start = pcbnew.wxPoint(FromMM(x + r), FromMM(y))
        dot = pcbnew.PCB_SHAPE(self.pcb)
        dot.SetShape(pcbnew.S_CIRCLE)
        dot.SetLayer(layer)
        dot.SetStart(start)
        dot.SetEnd(start)
        dot.SetWidth(width)
        dot.SetCenter(center)
        dot.SetFilled(True)
        return dot

    def RefillBoardAreas(self):
        for i in range(self.pcb.GetAreaCount()):
            area = self.pcb.GetArea(i)
            area.ClearFilledPolysList()
            area.UnFill()
        filler = pcbnew.ZONE_FILLER(self.pcb)
        filler.Fill(self.pcb.Zones())
