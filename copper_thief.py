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
                    filename="/home/mrussell/logs/thief.log",
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
                    logger.info(f"Applying dots to {zonename} with spacing {spacing} and radius: {radius}")
                    dotter.apply_dots(zone, spacing=spacing, radius=radius)
                    #board.Remove(zone)
                else:
                    wx.MessageBox("Zone name must be \"theiving\".", "Check zone name.", wx.OK)
        aParameters.Destroy()


class Dotter():

    def __init__(self):
        self.pcb = pcbnew.GetBoard()

    def apply_dots(self, zone, spacing=2, radius=0.5):
        """Iterate over the zone area and add dots if inside the zone."""
        zones = self.pcb.Zones()
        layer = zone.GetLayer()
        
        # Get the zone outline and deflate it so we don't put dots to close to the outside
        zone_outline = zone.Outline()
        zone_outline.Deflate(FromMM(radius), 16, pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS)
        zone.SetOutline(zone_outline)
        
        
        bbox = zone.GetBoundingBox()
        zonepolys = zone.GetFilledPolysList(layer)
        logger.info(f"Zone polys , {str(zonepolys)}")
        # Increase the clearance so we move even further away from existing copper
        clearance = zone.GetLocalClearance()
        zone.SetLocalClearance(clearance + int(radius * 1e6))
        zone.SetNeedRefill(True)
        filler = pcbnew.ZONE_FILLER(self.pcb)
        filler.Fill(zones)

        # Find any keep out zones to check later when we're dotting
        keep_out_zones = []
        for koz in zones:
            if koz.GetIsRuleArea():
                keep_out_zones.append(koz)
                logger.info("Added Keepout Zone")
        
        # Iterate over the bounding box of the chosen zone
        for x in np.arange(bbox.GetLeft() / 1e6, bbox.GetRight() / 1e6, spacing):
            for y in np.arange(bbox.GetTop() / 1e6, bbox.GetBottom() / 1e6, spacing):
                # If the dot centre is inside the the deflated zone poly, we're ok to place a dot
                logger.info(f"Try {x},{y}")
                if zone.HitTestFilledArea(layer, pcbnew.VECTOR2I(FromMM(x), FromMM(y))): 
    #                if zonepolys.Collide(pcbnew.VECTOR2I(FromMM(x), FromMM(y))):#, FromMM(radius)):
                    logger.info(f"  In Zone")                    
                    # Check that the dot wont touch any keep out zones
                    touch_keepout = False
                    for koz in keep_out_zones:
                        if koz.Outline().Collide(pcbnew.VECTOR2I(FromMM(x), FromMM(y)), FromMM(radius)):
                            touch_keepout = True
                            
                    if not touch_keepout:
                        dot = self.create_dot(layer, x, y, radius, 1)
                        self.pcb.Add(dot)
        
        # Reset the zone clearance
        zone.SetLocalClearance(clearance)
        zone.SetNeedRefill(True)
        filler = pcbnew.ZONE_FILLER(self.pcb)
        filler.Fill(self.pcb.Zones())
        pcbnew.Refresh()
        # self.RefillBoardAreas()

    def create_dot(self, layer, x, y, r, width):
        """Create a dot."""
        logger.info(f"Creating dot at {x}, {y} with radius {r}")

        center = pcbnew.VECTOR2I(FromMM(x), FromMM(y))
        start = pcbnew.VECTOR2I(FromMM(x + r), FromMM(y))
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
