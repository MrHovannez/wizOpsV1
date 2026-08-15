from __future__ import annotations
from pathlib import Path
import json, re
from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import DataTable, Footer, Header, Input, Label, Static
from textual.widget import Widget
from wizops.config import DB_PATH
from wizops.events.archive import ArchiveStore
from datetime import datetime
from wizops.platform.storage import StorageProvider

from wizops.platform.linux.linux_platform import LinuxPlatform
from wizops.application.system import SystemService
from wizops.application import WizardingOpsApplication
from wizops.application.models import EventQuery

from wizops.presentation.formatting import human_size
from wizops.presentation.renderers.services import ServicesRenderer
from wizops.presentation.renderers.health import HealthRenderer
from wizops.presentation.renderers.capacity import CapacityRenderer
from wizops.presentation.renderers.collection import CollectionRenderer
from wizops.presentation.renderers.database import DatabaseRenderer
from wizops.presentation.renderers.system import SystemRenderer
from wizops.presentation.renderers.latest import LatestRenderer
from wizops.presentation.renderers.current_services import CurrentServicesRenderer


from wizops.presentation.formatting import (
    COLORS,
    SEVS,
    clean,
    clean_timestamp,
    human_size,
    local_timestamp,
    summary,
    pretty_raw
)


import os
import shutil
import socket
import subprocess

def sev_text(v): return Text(str(v),style=COLORS.get(v,""))

def diagnose(row):
    blob=(clean(row["message"])+" "+clean(row["raw_event"])).lower()
    service=clean(row["service"])
    if "401" in blob and ("api key" in blob or "authentication" in blob or "unauthorized" in blob):
        return ("auth_credential_failure.v1","AUTH / CREDENTIAL FAILURE","HIGH",
                "The service reached an API endpoint but authentication was rejected.",
                "Verify the configured API key/secret source, confirm the container or service received the intended value, then retry one request. Do not paste secrets into Console.",
                "Correct the credential source or secret injection path only after confirming which service is receiving the wrong or missing value.")
    if "out of memory" in blob or "cudamalloc failed" in blob:
        return ("gpu_memory_pressure.v1","GPU MEMORY PRESSURE","HIGH",
                "CUDA allocation failed while a model or projector was starting/loading.",
                "Check current VRAM consumers with ai gpu/model loaded. Unload competing models or reduce GPU offload/context pressure, then retry. Correlate nearby Ollama/llama events before changing defaults.",
                "Free competing VRAM or reduce the failing workload's GPU memory demand, then retry once and verify the allocation failure stops.")
    if "terminated" in blob and ("signal: killed" in blob or "core dumped" in blob or "aborted" in blob):
        return ("process_termination.v1","PROCESS TERMINATION","HIGH",
                "A model server exited because of a signal or abnormal termination.",
                "Inspect RELATED events immediately before this record for OOM/allocation failures. Check journal/coredump evidence before restarting repeatedly.",
                "Remedy the upstream termination cause first. Restart only the affected service after OOM, signal, or coredump evidence has been reviewed.")
    if "deprecated" in blob:
        return ("deprecated_configuration.v1","DEPRECATED CONFIGURATION","MEDIUM",
                "A service accepted a setting or flag that is deprecated.",
                "Identify the replacement named in the message, update the source configuration during a maintenance pass, and verify the warning disappears after restart.",
                "Replace the deprecated setting with the supported replacement named by the service and verify the warning disappears.")
    if "timeout" in blob or "timed out" in blob or "deadline exceeded" in blob:
        return ("timeout_deadline.v1","TIMEOUT / DEADLINE","MEDIUM",
                "An operation exceeded its allowed response or watchdog window.",
                "Check RELATED events for resource pressure or a slow dependency. Confirm the target service is healthy before increasing timeout values.",
                "Fix the slow or unavailable dependency when identified. Increase timeout values only when the observed healthy operation legitimately needs more time.")
    if "connection handling canceled" in blob or "operation was aborted" in blob:
        return ("request_cancellation.v1","CLIENT / REQUEST CANCELLATION","LOW",
                "The request was canceled or disconnected before normal completion.",
                "If isolated, treat as informational noise. If repeated, correlate timestamps with client disconnects, proxy behavior, and model latency.",
                "No change is recommended for an isolated cancellation. For repeated events, remedy the confirmed client, proxy, or latency cause.")
    if "transaction in progress" in blob:
        return ("database_transaction_state.v1","DATABASE TRANSACTION STATE","MEDIUM",
                "The database reported an unexpected transaction state.",
                "Review adjacent Vector DB events and the caller lifecycle. Repeated occurrences may indicate transaction cleanup or retry handling that needs correction.",
                "Correct transaction cleanup or retry lifecycle only after repeated correlated occurrences confirm the pattern.")
    return ("none","UNCLASSIFIED EVENT","REVIEW",
            f"Console has no specific remedy rule for this {service} event yet.",
            "Inspect MESSAGE, RAW EVENT, and RELATED context. If this pattern repeats, promote it into a Console diagnosis rule after confirming the root cause.",
            None)

BRAILLE_DOTS=((0x01,0x08),(0x02,0x10),(0x04,0x20),(0x40,0x80))

def _braille(pixels,cx,cy):
    bits=0; x0=cx*2; y0=cy*4
    for dy in range(4):
        for dx in range(2):
            if (x0+dx,y0+dy) in pixels: bits|=BRAILLE_DOTS[dy][dx]
    return chr(0x2800+bits) if bits else " "

class NeonChart(Widget):
    """Composition-first Braille chart renderer for dense terminal dashboards."""
    can_focus=False

    def __init__(self, *, mode="line", palette=None, id=None, classes=None):
        super().__init__(id=id, classes=classes)
        self.mode=mode
        self.palette=palette or ["#00eaff"]
        self.series=[]
        self.labels=[]
        self.caption=""
        self.stats=""

    def set_data(self, series, *, labels=None, caption="", stats=""):
        self.series=[list(map(float, s)) for s in series]
        self.labels=list(labels or [])
        self.caption=caption
        self.stats=stats
        self.refresh(layout=False)

    @staticmethod
    def _percentile(values, q):
        vals=sorted(v for v in values if v > 0)
        if not vals:
            return 1.0
        return vals[min(len(vals)-1, int((len(vals)-1)*q))] or 1.0

    @staticmethod
    def _resample_sum(values, width):
        if width <= 0:
            return []
        if not values:
            return [0.0]*width
        out=[]
        n=len(values)
        for x in range(width):
            lo=int(x*n/width)
            hi=max(lo+1, int((x+1)*n/width))
            out.append(sum(values[lo:hi]))
        return out

    @staticmethod
    def _active_window(values, pad=3):
        nz=[i for i,v in enumerate(values) if v > 0]
        if not nz:
            return list(values), 0, max(0, len(values)-1)
        lo=max(0, nz[0]-pad)
        hi=min(len(values)-1, nz[-1]+pad)
        return list(values[lo:hi+1]), lo, hi

    @staticmethod
    def _line_pixels(values, pw, ph, ceiling=None):
        if not values:
            return set()
        ceiling=ceiling or max(values) or 1.0
        vals=NeonChart._resample_sum(values, pw)
        pts=[]
        for x,v in enumerate(vals):
            y=ph-1-int(round(min(v,ceiling)/ceiling*(ph-1)))
            pts.append((x,max(0,min(ph-1,y))))
        pix=set()
        for i,(x1,y1) in enumerate(pts):
            if i == 0:
                pix.add((x1,y1))
                continue
            x0,y0=pts[i-1]
            dx=abs(x1-x0); dy=abs(y1-y0)
            sx=1 if x0<x1 else -1
            sy=1 if y0<y1 else -1
            err=dx-dy
            x,y=x0,y0
            while True:
                pix.add((x,y))
                if x==x1 and y==y1:
                    break
                e2=2*err
                if e2>-dy:
                    err-=dy; x+=sx
                if e2<dx:
                    err+=dx; y+=sy
        return pix

    @staticmethod
    def _bar_pixels(values, pw, ph, ceiling):
        vals=NeonChart._resample_sum(values, pw)
        pix=set()
        for x,v in enumerate(vals):
            if v <= 0:
                continue
            h=max(1, int(round(min(v,ceiling)/ceiling*(ph-1))))
            for y in range(ph-1, max(-1, ph-2-h), -1):
                if 0 <= y < ph:
                    pix.add((x,y))
        return pix

    def _render_activity(self, width, height):
        out=Text(); out.append(self.caption+"\n",style="bold #62f5ff")
        values=self.series[0] if self.series else []
        cw=max(32,width-7); rows=max(5,height-4); pw=cw*2; ph=rows*4
        ceiling=self._percentile(values,.95); pix=self._bar_pixels(values,pw,ph,ceiling)
        guides={0,cw//4,cw//2,(cw*3)//4,cw-1}
        for cy in range(rows):
            out.append("│",style="#164d9b")
            for cx in range(cw):
                ch=_braille(pix,cx,cy)
                if ch!=" ": out.append(ch,style="bold #ff62ec" if cy==0 else "bold #00eaff")
                elif cx in guides: out.append("┊",style="#12395b")
                elif cy in (rows//3,(rows*2)//3): out.append("╌",style="#0b2d4c")
                else: out.append(" ")
            out.append("\n")
        out.append("└"+"─"*cw+"\n",style="#164d9b")
        axis=[" "]*cw
        for pos,label in ((0,"24h ago"),(cw//4,"18h"),(cw//2,"12h"),((cw*3)//4,"6h"),(cw-3,"now")):
            pos=max(0,min(cw-len(label),pos))
            for i,ch in enumerate(label): axis[pos+i]=ch
        out.append(" "+"".join(axis)+"\n",style="#7395b2")
        if self.stats: out.append(self.stats,style="bold #55ff9a")
        return out

    def _render_lanes(self, width, height):
        out=Text(); out.append(self.caption+"\n",style="bold #ff6a9a")
        n=max(1,len(self.series)); lane_rows=max(3,max(9,height-4)//n)
        cw=max(24,width-30); pw=cw*2
        for i,values in enumerate(self.series):
            color=self.palette[i%len(self.palette)]
            label=self.labels[i] if i<len(self.labels) else f"S{i+1}"
            ceiling=self._percentile(values,.95); vals=self._resample_sum(values,pw); ph=lane_rows*4
            pts=[(x,max(0,min(ph-1,ph-1-int(round(min(v,ceiling)/ceiling*(ph-1)))))) for x,v in enumerate(vals)]
            pix=set()
            if pts:
                px,py=pts[0]; pix.add((px,py))
                for x,y in pts[1:]:
                    for xx in range(min(px,x),max(px,x)+1): pix.add((xx,py))
                    for yy in range(min(py,y),max(py,y)+1): pix.add((x,yy))
                    px,py=x,y
            total=sum(values); peak=max(values,default=0)
            for cy in range(lane_rows):
                out.append(f"{label:<7}" if cy==0 else "       ",style=f"bold {color}"); out.append("│",style="#27395b")
                for cx in range(cw):
                    ch=_braille(pix,cx,cy)
                    if ch!=" ": out.append(ch,style=f"bold {color}")
                    elif cx in (cw//4,cw//2,(cw*3)//4): out.append("┊",style="#17243b")
                    elif cy==lane_rows-1: out.append("╌",style="#17243b")
                    else: out.append(" ")
                out.append("│",style="#27395b")
                if cy==0: out.append(f" {total:>5,.0f}  peak {peak:>4,.0f}",style=color)
                out.append("\n")
        if self.stats: out.append(self.stats,style="bold #55ff9a")
        return out

    def render(self):
        width=max(24,self.size.width)
        height=max(8,self.size.height)
        if not self.series:
            return Text("No telemetry in selected window",style="#52799c")
        if self.mode=="activity":
            return self._render_activity(width,height)
        if self.mode=="lanes":
            return self._render_lanes(width,height)

        # Generic single-series fallback.
        out=Text()
        if self.caption:
            out.append(self.caption+"\n",style="bold #62f5ff")
        values=self.series[0]
        cw=max(18,width-4)
        rows=max(4,height-4)
        pix=self._line_pixels(values,cw*2,rows*4,self._percentile(values,.95))
        color=self.palette[0]
        for cy in range(rows):
            out.append("│",style="#164d9b")
            for cx in range(cw):
                out.append(_braille(pix,cx,cy),style=f"bold {color}")
            out.append("\n")
        out.append("└"+"─"*cw+"\n",style="#164d9b")
        if self.stats:
            out.append(self.stats,style="bold #55ff9a")
        return out

class ConsoleApp(App):
    TITLE="⚡ Hov the Wizard presents: Wizarding Operations v1.1  ⚡"
    CSS=r"""
    Screen { background: #020712; color: #d8e7ff; }
    Header { background: #09041a; color: #62f5ff; text-style: bold; }
    #metrics { height: 5; padding: 0 1; }
    .metric { width: 1fr; height: 5; border: round #4b2b7f; margin-right: 1; content-align: center middle; text-style: bold; }
    #merr { border: round #ff416c; color: #ff416c; }
    #mwarn { border: round #ffb000; color: #ffb000; }
    #minfo { border: round #00d9ff; color: #00d9ff; }
    #mtotal { border: round #d65cff; color: #d65cff; }
    #intel { height: 5; padding: 0 1; }
    #topservices { width: 4fr; border: heavy #00d9ff; background: #020b18; color: #62f5ff; padding: 0 1; margin-right: 1; }
    #attentioncard { width: 1fr; border: heavy #ff3de8; background: #100318; color: #ff62ec; padding: 0 1; text-style: bold; }
    #filters { height: 3; padding: 0 1; }
    #status { width: 1fr; border: round #00d9ff; padding: 0 1; color: #62f5ff; }
    #search { display: none; width: 2fr; border: round #d65cff; }
    #search.visible { display: block; }
    #body { height: 1fr; padding: 0 1; }
    #tablepane { width: 2fr; border: round #00aeea; }
    #detailpane { width: 1fr; border: round #7c3cff; padding: 0 1; overflow-y: auto; }

    #dashboardpane {
        height: 1fr;
    }

    .dashboard #dashboardpane {
        display: block;
    }

    .events #dashboardpane,
    .overview #dashboardpane {
        display: none;
    }

    /* Dashboard workspace */
    .dashboard #intel {
        height: 7fr;
        min-height: 7fr;
    }



    /* Dashboard status area */

    #dashboard_status {
        height: 1fr;
        min-height: 16;
        width: 1fr;
        margin: 0;
        padding: 0;
    }

    #dashboard_status_left {
        width: 2fr;
        min-width: 0;
        height: 1fr;
        margin: 0;
        padding: 0;
    }

    #dashboard_status_right {
        width: 1fr;
        min-width: 0;
        height: 1fr;
        margin: 0 0 0 1;
        padding: 0;
    }

    .dashboard #topservices {
        width: 1fr;
        height: 1fr;
        min-height: 14;
        margin: 0;
        border: round #ffb000;
        padding: 1 2;
    }

    .dashboard #dashboardsystem {
        width: 1fr;
        height: 1fr;
        min-height: 14;
        margin: 0;
        border: round #00d9ff;
        padding: 1 2;
    }

    /* Dashboard event feed */
    .dashboard #body {
        height: 13;
        min-height: 13;
    }

    .dashboard #tablepane {
        width: 1fr;
        border: round #ff416c;
    }

    .dashboard #detailpane {
        display: none;
    }

    .dashboard #events {
        height: 1fr;
    }

    #dashboard_widgets {
        height: 15;
        min-height: 15;
        margin: 1 0;
    }

    #currentservices {
        width: 1fr;
        min-width: 0;
        border: round #00d9ff;
        padding: 1 2;
    }

    #dashboardactivity {
        width: 1fr;
        min-width: 0;
        border: round #d65cff;
        padding: 1 2;
    }

    #dashboardsystem {
        width: 3fr;
        border: round #00d9ff;
        padding: 1 2;
    }

    #eventanalysis {
        display: none;
        width: 1fr;
        border: round #ff3de8;
        background: #080313;
        padding: 0 1;
        margin: 0 1;
        overflow-y: auto;
    }
    #analysistitle {
        height: 2;
        color: #ff62ec;
        text-style: bold;
        padding: 0 1;
    }
    #analysis {
        color: #e6f4ff;
        border: round #00d9ff;
        background: #020b18;
        padding: 1 1;
        margin: 0 1 1 1;
    }
    #detailtitle { color: #62f5ff; text-style: bold; height: 2; }
    #detail, #messageview, #rawview, #relatedview { color: #e6f4ff; padding: 0 1; }
    .sectiontitle { height: 2; color: #00eaff; text-style: bold; padding: 0 1; }
    .inspectbox { border: round #075a88; background: #020b18; margin: 0 1; padding: 0 1; }
    #detail { height: 10; border: round #087dba; }
    #messageview { height: 7; border: round #164d9b; }
    #rawview { height: 14; border: round #00b8c8; color: #66ff9f; overflow-y: auto; }
    #relatedview { height: 1fr; min-height: 7; border: round #7c3cff; color: #ff79ed; overflow-y: auto; }
    DataTable { height: 1fr; background: #020712; }
    DataTable > .datatable--header { background: #07182a; color: #62f5ff; text-style: bold; }
    DataTable > .datatable--cursor { background: #003f66; color: white; text-style: bold; }
    #viewbar { height: 2; padding: 0 2; color: #d65cff; text-style: bold; }
    Footer { background: #09041a; color: #d8e7ff; }
    .events #metrics { height: 3; }
    .events .metric { height: 3; border: none; margin-right: 2; }
    .events #metrics { display: none; }
    .events #intel { display: none; }
    .events #detailpane { display: none; }
    .events #eventanalysis { display: block; }
    .events #tablepane { width: 3fr; border: round #d65cff; }
    .dashboard #tablepane { width: 2fr; border: round #ff416c; }
    .dashboard #detailpane { width: 1fr; border: round #ffb000; }
    .events #eventanalysis { border: round #d65cff; background: #050814; }
    .events DataTable > .datatable--header { background: #120525; color: #ff79ed; }
    .events DataTable > .datatable--cursor { background: #4b126e; color: white; }
    .dashboard DataTable > .datatable--header { background: #180b0e; color: #ff8dbd; }
    """
    BINDINGS=[
        Binding("1","dashboard","Dashboard"),Binding("2","events","Events"),
        Binding("d","dashboard","Dashboard",show=False),Binding("e","events","Events",show=False),
        Binding("q","quit","Quit"),Binding("r","refresh_events","Refresh"),
        Binding("/","search","Search"),Binding("c","clear_filters","Clear"),
        Binding("s","cycle_service","Service"),Binding("v","cycle_severity","Severity"),
        Binding("a","all_events","All"),Binding("t","cycle_time_range","Time Range"),Binding("enter","focus_detail","Inspector"),
        Binding("space","toggle_mark","Mark",show=False),
        Binding("y","copy_selected","Copy Selected",show=False),
        Binding("x","export_selected","Export Selected"),
        Binding("shift+x","export_filtered","Export Filtered"),
        Binding("ctrl+x","export_all","Export All",show=False),
    ]
    def __init__(self, db_path=DB_PATH):
        super().__init__()

        self.db_path = Path(db_path)

        self.store = None
        self.platform = LinuxPlatform()
        self.system = None
        self.application = None
        self.service = None
        self.severity = "ATTENTION"
        self.search_text = None
        self.rows = {}
        self.marked_rows = set()
        self.view = "dashboard"
        self.time_range = "24H"

    def compose(self)->ComposeResult:
        yield Header()
        with Horizontal(id="metrics"):
            yield Static("",id="merr",classes="metric")
            yield Static("",id="mwarn",classes="metric")
            yield Static("",id="minfo",classes="metric")
            yield Static("",id="mtotal",classes="metric")
        with Vertical(id="dashboardpane"):

            # -------------------------------------------------
            # DASHBOARD STATUS AREA
            # -------------------------------------------------
            #
            # Large left area:
            #   TOP SERVICES
            #
            # Narrow right area:
            #   ATTENTION
            #   SYSTEM AT A GLANCE
            #
            # -------------------------------------------------

            with Horizontal(id="dashboard_status"):

                # ---------------------------------------------
                # LEFT: TOP SERVICES + EVENT HEALTH
                # ---------------------------------------------

                with Vertical(id="dashboard_status_left"):

                    yield Static(
                        "",
                        id="topservices",
                    )


                # ---------------------------------------------
                # RIGHT: ATTENTION + SYSTEM
                # ---------------------------------------------

                with Vertical(id="dashboard_status_right"):
                    yield Static(
                        "",
                        id="dashboardsystem",
                    )

            # -------------------------------------------------
            # DASHBOARD ACTIVITY AREA
            # -------------------------------------------------
            #
            # Only the live services inventory and event
            # activity chart live here.
            #
            # -------------------------------------------------

            with Horizontal(id="dashboard_widgets"):

                yield Static(
                    "",
                    id="currentservices",
                )

                yield NeonChart(
                    mode="activity",
                    palette=[
                        "#00eaff",
                        "#d65cff",
                        "#38f2ff",
                    ],
                    id="dashboardactivity",
                )


        with Horizontal(id="filters"):
            yield Label("",id="status")
            yield Input(
                placeholder="Search events… Enter applies • Esc cancels",
                id="search",
            )
        yield Label("",id="viewbar")
        with Horizontal(id="body"):
            with Vertical(id="tablepane"):
                yield DataTable(id="events",cursor_type="row",zebra_stripes=True)
            with Vertical(id="eventanalysis"):
                yield Label("⚕ FORENSIC INVESTIGATION",id="analysistitle")
                yield Static("Select an event",id="analysis")
            with Vertical(id="detailpane"):
                yield Label("▣ EVENT DETAILS",id="detailtitle")
                yield Static("Select an event",id="detail",classes="inspectbox")
                yield Label("▣ MESSAGE  (summary)",classes="sectiontitle")
                yield Static("Select an event",id="messageview",classes="inspectbox")
                yield Label("▣ RAW EVENT  (exact)",classes="sectiontitle")
                yield Static("Select an event",id="rawview",classes="inspectbox rawbox")
                yield Label("⌁ RELATED  (context)",classes="sectiontitle")
                yield Static("Select an event",id="relatedview",classes="inspectbox relatedbox")
        yield Footer()

    def on_mount(self):
        self.store=ArchiveStore(self.db_path)
        self.store.init_schema()
        self.system = SystemService(self.platform)
        self.application = WizardingOpsApplication(
        self.platform,
        self.store,
        self.db_path,
        )
        self.add_class("dashboard")


        table = self.query_one("#events", DataTable)

        check_col, time_col, severity_col, service_col, message_col = table.add_columns(
            "✓",
            "Time (Local)",
            "Severity",
            "Service",
            "Message (summary)",
        )

        table.columns[check_col].width = 4
        table.columns[time_col].width = 19
        table.columns[severity_col].width = 9
        table.columns[service_col].width = 20


        self.refresh_events()
        table.focus()

        # Keep live dashboard telemetry updated independently
        # from the event table.
        self.set_interval(
            3.0,
            self.refresh_dashboard_telemetry,
        )

    def on_unmount(self):
        if self.store: self.store.close()

    def refresh_dashboard_telemetry(self):
            """
            Refresh live dashboard telemetry without rebuilding the event table.

            This keeps system resources and running services live while avoiding
            unnecessary event/database refreshes every few seconds.
            """

            # -------------------------------------------------
            # LIVE RUNNING SERVICES
            # -------------------------------------------------

            service_inventory = self.platform.services.snapshot()

            current_services = self.query_one("#currentservices")

            print(
                "CURRENT SERVICES SIZE:",
                current_services.content_size,
            )

            current_services.update(
                CurrentServicesRenderer.render(
                    service_inventory.services
                )
            )
            # -------------------------------------------------
            # LIVE SYSTEM STATUS
            # -------------------------------------------------

            overview = self.application.overview()
            system_status = overview.system()
            system_panel = SystemRenderer.render(system_status)

            dashboard_widget = self.query_one("#dashboardsystem")

            dashboard_widget.styles.border = (
                "round",
                system_panel.border_color,
            )

            dashboard_widget.update(
                system_panel.text
            )

            # -------------------------------------------------
            # LIVE TOP SERVICES
            # -------------------------------------------------

            top_status = self.application.overview().services()
            top_widget = self.query_one("#topservices")

            top_panel = ServicesRenderer.render(
                top_status,
                top_widget.content_region.width,
            )

            top_widget.styles.border = (
                "round",
                top_panel.border_color,
            )

            top_widget.update(
                top_panel.text,
            )

    def refresh_events(self):

        # Build query
        query = EventQuery(
            service=self.service,
            severity=self.severity,
            search=self.search_text,
            time_window=self.time_range,
        )

        rows = self.application.events(query).events

        table = self.query_one("#events", DataTable)

        table.clear()
        self.rows = {}


        for row in rows:
            key = str(row["id"])
            self.rows[key] = row

            table.add_row(
                Text("✓", style="bold white on #2a8f2a")
                if key in self.marked_rows
                else Text(" "),
                Text(local_timestamp(clean(row["timestamp"]))),
                sev_text(row["severity"]),
                Text(clean(row["service"])),
                Text(summary(row["message"])),
                key=key,
            )


        overview = self.application.overview()
        metrics = overview.metrics()

        service_inventory = self.platform.services.snapshot()
        current_services = self.query_one("#currentservices")

        self.query_one("#currentservices").update(
            CurrentServicesRenderer.render(
                service_inventory.services,
                current_services.content_size.width,
            )
        )

        err = metrics.errors
        warn = metrics.warnings
        info = metrics.info
        total = metrics.total

        self.query_one("#merr").update(f"▣ ERRORS\n{err}")
        self.query_one("#mwarn").update(f"▲ WARNINGS\n{warn}")
        self.query_one("#minfo").update(f"● INFO\n{info:,}")
        self.query_one("#mtotal").update(f"◈ TOTAL EVENTS\n{total:,}")

        # EVENT ACTIVITY v7: dense telemetry chart.
        activity = self.store.activity_last_24h()
        bucket_map = {
            int(b): int(n)
            for b, n in activity
            if b is not None and 0 <= int(b) < 96
        }
        vals = [bucket_map.get(i, 0) for i in range(96)]

        peak = max(vals, default=0)
        total_activity = sum(vals)
        avg = (total_activity / 24) if vals else 0
        current = sum(vals[-4:]) if len(vals) >= 4 else sum(vals)

        graph_width = 88
        compressed = []

        for x in range(graph_width):
            lo = int(x * len(vals) / graph_width)
            hi = max(lo + 1, int((x + 1) * len(vals) / graph_width))
            compressed.append(sum(vals[lo:hi]))

        nonzero = sorted(v for v in compressed if v > 0)

        if nonzero:
            p90 = nonzero[
                min(len(nonzero) - 1, int((len(nonzero) - 1) * 0.90))
            ]
            p95 = nonzero[
                min(len(nonzero) - 1, int((len(nonzero) - 1) * 0.95))
            ]
            visual_ceiling = max(1, p95)
        else:
            p90 = p95 = visual_ceiling = 1

        graph_rows = 10

        def cell_units(value,row_from_top):
            if value <= 0:
                return 0
            # Robust scaling: preserve low/medium activity while clipping only
            # the visual height of extreme spikes. Exact peak stays in metrics.
            shown=min(value,visual_ceiling)
            units=(shown/visual_ceiling)*(graph_rows*8)
            row_bottom=graph_rows-1-row_from_top
            return max(0,min(8,int(round(units-row_bottom*8))))

        self.query_one("#dashboardactivity",NeonChart).set_data(
            [vals],
            caption="▥ EVENT ACTIVITY  •  LAST 24H  •  15 MIN BUCKETS",
            stats=f"PEAK {peak:,}/15m   │   P95 {visual_ceiling:,}   │   AVG {avg:,.1f}/hour   │   CURRENT HOUR {current:,}   │   TOTAL {total_activity:,}",
        )


        latest = self.store.latest_attention()
        self.latest_attention_id=int(latest["id"]) if latest else None

        system_status = overview.system()
        system_panel = SystemRenderer.render(system_status)

        dashboard_widget = self.query_one("#dashboardsystem")
        dashboard_widget.styles.border = (
            "round",
            system_panel.border_color,
        )
        dashboard_widget.update(system_panel.text)


        top_status = self.application.overview().services()

        top_widget = self.query_one("#topservices")

        top_panel = ServicesRenderer.render(
            top_status,
            top_widget.content_region.width,
        )

        top_widget.styles.border = (
            "round",
            top_panel.border_color,
        )

        top_widget.update(
            top_panel.text
        )

        hidden=max(total-len(rows),0)
        svc=self.service or "ALL"; sev=self.severity or "ALL"; search=self.search_text or "—"
        self.query_one("#status").update(f" SERVICE: {svc}   •   SEVERITY: {sev}   •   TIME: {self.time_range}   •   SEARCH: {search}")
        purpose={"dashboard":"OPERATIONS • WHAT IS WRONG NOW?","events":"FORENSICS • WHAT HAPPENED AND WHY?"}[self.view]
        self.query_one("#viewbar").update(f"VIEW: {self.view.upper()}   •   {purpose}   •   {len(rows)} EVENTS SHOWN   •   DB: {self.db_path}")
        if rows: self._show_detail(rows[0])

    def _selected(self):
        table=self.query_one("#events",DataTable)
        if not table.row_count or table.cursor_row<0: return None
        key=str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)
        return self.rows.get(key)
    def _show_detail(self,row):
        if not row: return
        raw=pretty_raw(row["raw_event"])

        text=Text()

        text.append(f"ID          {row['id']}\n",style="#ff62ec")
        text.append(f"TIME        {local_timestamp(row["timestamp"])}\n",style="#62f5ff")
        text.append("SEVERITY    "); text.append(f"{row['severity']}\n",style=COLORS.get(row["severity"],""))
        text.append(f"SERVICE     {row['service']}\n")
        text.append(f"SOURCE      {row['source_type']} · {row['source']}\n")
        if row["category"]: text.append(f"CATEGORY    {row['category']}\n")
        if row["model"]: text.append(f"MODEL       {row['model']}\n")
        if row["request_id"]: text.append(f"REQUEST     {row['request_id']}\n")

        self.query_one("#detail").update(text)

        msg=Text()

        msg.append(summary(row["message"],3000))
        self.query_one("#messageview").update(msg)

        raw_text=Text()

        raw_text.append(raw)
        self.query_one("#rawview").update(raw_text)

        related = self.store.related_events(
            event_id=row["id"],
            service=row["service"],
            category=row["category"],
            request_id=row["request_id"],
            model=row["model"],
        )

        rel = Text()

        rel.append(
            "scored relation: request 100 · model 40 · category 30 · service 10\n",
            style="dim",
        )

        if not related:
            rel.append("No related events found.", style="dim")

        for item in related:
            rel.append(
                f"#{item['id']}  {local_timestamp(clean(item['timestamp']))}  "
            )
            rel.append(
                f"{item['severity']:<5}",
                style=COLORS.get(item["severity"], ""),
            )
            rel.append(
                f"  score={item['relation_score']:<3}  "
                f"{item['service']:<12}  "
                f"{summary(item['message'],82)}\n"
            )

        self.query_one("#relatedview").update(rel)

        rule,kind,risk,why,remedy,possible_remedy = diagnose(row)

        ana = Text()

        ana.append("EVENT IDENTITY / CLASSIFICATION\n", style="bold #62f5ff")
        ana.append(kind + "\n", style="bold #ff62ec")
        ana.append(f"PRIORITY  {risk}\n", style=COLORS.get(row["severity"], "#ffb000"))
        ana.append(f"RULE      {rule}\n\n", style="#7f9bb8")

        ana.append("DIAGNOSIS BASIS\n", style="bold #62f5ff")
        ana.append(why + "\n\n")

        ana.append("RECOMMENDED NEXT ACTION\n", style="bold #55ff9a")
        ana.append(remedy + "\n\n")

        if possible_remedy:
            ana.append("POSSIBLE REMEDY\n", style="bold #ff62ec")
            ana.append(possible_remedy + "\n\n")
        else:
            ana.append("NO VERIFIED REMEDY\n", style="bold #ff416c")
            ana.append(
                "Console does not have enough deterministic evidence to recommend a configuration change for this event.\n\n"
            )

        ana.append(f"CONFIDENCE\n{risk}\n\n", style="bold #62f5ff")

        fingerprint = summary(row["message"], 80)

        pattern_rows = self.store.pattern_summary(
            row["service"],
            clean(row["message"]),
        )
        ana.append("OCCURRENCE\n",style="bold #ffb000")
        ana.append(f"First seen: {pattern_rows[0] or '—'}\nLast seen:  {pattern_rows[1] or '—'}\nCount:      {pattern_rows[2]:,}\n\n")
        ana.append("EVIDENCE SUMMARY\n",style="bold #62f5ff")
        ana.append(f"Service: {row['service']}\nSeverity: {row['severity']}\nCategory: {row['category'] or '—'}\nRelated events: {len(related)}\n\n")
        ana.append("Console guidance is rule-based and evidence-linked; verify the raw event and related records before applying a configuration change.",style="dim")
        self.query_one("#analysis").update(ana)

    def on_data_table_row_highlighted(self,event:DataTable.RowHighlighted):
        self._show_detail(self._selected())
    def action_focus_detail(self):
        self._show_detail(self._selected())
        if self.view=="dashboard": self.query_one("#detailpane").focus()
    def action_dashboard(self):
        self.view="dashboard"; self.remove_class("events"); self.add_class("dashboard"); self.refresh_events()
    def action_events(self):
        self.view="events"; self.remove_class("dashboard"); self.add_class("events"); self.refresh_events()

    def action_refresh_events(self):
        # Re-run unified ingestion before refreshing
        try:
            from wizops.application import refresh
            result = refresh(self.store)
            # Display summary of what was ingested
            self.notify(
                f"Refresh complete: {result.inserted} inserted, {result.deduplicated} deduplicated",
                severity="info",
            )

            if result.errors:
                self.notify(
                    f"{len(result.errors)} errors occurred during refresh",
                    severity="warning",
                )
        except Exception as e:
            self.notify(f"Refresh failed: {e}", severity="error")
        self.refresh_events()
    def action_search(self):
        box=self.query_one("#search",Input); box.add_class("visible"); box.value=self.search_text or ""; box.focus()
    def on_input_submitted(self,event:Input.Submitted):
        self.search_text=event.value.strip() or None; event.input.remove_class("visible"); self.query_one("#events").focus(); self.refresh_events()
    def on_click(self, event):
        wid=getattr(getattr(event, "widget", None), "id", None)
        metric={"merr":"ERROR","mwarn":"WARN","minfo":"INFO","mtotal":None}
        if wid in metric:
            self.severity=metric[wid]
            self.view="dashboard"
            self.remove_class("events")
            self.add_class("dashboard")
            self.refresh_events()
            return

    def on_key(self,event):
        if event.key=="escape" and self.query_one("#search",Input).has_focus:
            self.query_one("#search",Input).remove_class("visible"); self.query_one("#events").focus()

    def _marked_events(self):
        return [self.rows[k] for k in self.rows if k in self.marked_rows]

    def action_toggle_mark(self):
        row=self._selected()
        if not row:
            return
        key=str(row["id"])
        if key in self.marked_rows:
            self.marked_rows.remove(key)
        else:
            self.marked_rows.add(key)
        self.refresh_events()
        table=self.query_one("#events",DataTable)
        try:
            table.move_cursor(row=table.get_row_index(key))
        except Exception:
            pass

    def _copy_row(self):
        return self._selected()

    def action_copy_selected(self):
        rows=self._marked_events()
        if not rows:
            row=self._copy_row()
            rows=[row] if row else []
        if not rows:
            self.notify("No event selected.",severity="warning"); return
        try:
            text = self.application.clipboard_text(rows)
            provider=self.application.copy(text)
            if provider: self.notify(f"Copied {len(rows)} event(s) • {provider}")
            else:
                fallback=Path("/tmp/wizops-copy.txt"); fallback.write_text(text)
                self.notify(f"Clipboard unavailable • wrote {fallback}",severity="warning")
        except Exception as e:
            self.notify(f"Clipboard failed: {e}", severity="error")

    def action_export_selected(self):
        if self.view!="events":
            self.notify("Export is available in Events view.",severity="warning"); return
        rows = self._marked_events()
        if not rows:
            row = self._selected()
            rows = [row] if row else []
            label = f"event-{row['id']}" if row else "event"
        else:
            label = "events-marked"
        result = self.application.export(
            rows,
            label,
            service=self.service,
            severity=self.severity,
            time_range=self.time_range,
            search=self.search_text,
        )
        self.notify(
            result.message,
            severity="information" if result.success else "warning",
        )

    def action_export_filtered(self):
        if self.view!="events":
            self.notify("Export is available in Events view.",severity="warning"); return
            query = EventQuery(
            service=self.service,
            severity=self.severity,
            search=self.search_text,
            time_window=self.time_range,
        )

        result = self.application.export(
            self.application.events(query).events,
            "events-filtered",
            service=self.service,
            severity=self.severity,
            time_range=self.time_range,
            search=self.search_text,
        )

        self.notify(
            result.message,
            severity="information" if result.success else "warning",
        )

    def action_export_all(self):
        if self.view!="events":
            self.notify("Export is available in Events view.",severity="warning"); return
            result = self.application.export(
            self.store.list_events(),
            "events-all",
            service=self.service,
            severity=self.severity,
            time_range=self.time_range,
            search=self.search_text,
        )

        self.notify(
            result.message,
            severity="information" if result.success else "warning",
        )


    def action_clear_filters(self): self.service=None; self.severity="ATTENTION"; self.search_text=None; self.refresh_events()
    def action_cycle_service(self):
        vals = [None] + self.application.services()
        self.service = vals[(vals.index(self.service) + 1) % len(vals)]
        self.refresh_events()
    def action_all_events(self):
        self.service = None
        self.severity = None
        self.refresh_events()
    def action_cycle_time_range(self):
        vals=["1H","6H","12H", "24H","7D","30D", "ALL"]
        self.time_range=vals[(vals.index(self.time_range)+1)%len(vals)]
        self.refresh_events()
    def action_cycle_severity(self):
        vals = ["ATTENTION", "WARN", "ERROR", "FATAL", "INFO", None]
        self.severity = vals[(vals.index(self.severity) + 1) % len(vals)]
        self.refresh_events()


def run(db_path=DB_PATH): ConsoleApp(db_path).run()
