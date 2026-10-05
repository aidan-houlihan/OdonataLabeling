import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth

LABEL_W, LABEL_H = 5 * inch, 3 * inch
PAGE_W, PAGE_H = letter
DEFAULT_SIZE, MIN_SIZE = 10, 6.5
PAD_X, PAD_TOP, PAD_BOTTOM, LINE_SPACING = .16*inch, .15*inch, .13*inch, 1.16

FONT_FAMILIES = {
    "Helvetica": {"normal":"Helvetica","bold":"Helvetica-Bold","italic":"Helvetica-Oblique","scientific":"Helvetica-BoldOblique"},
    "Times": {"normal":"Times-Roman","bold":"Times-Bold","italic":"Times-Italic","scientific":"Times-BoldItalic"},
    "Courier": {"normal":"Courier","bold":"Courier-Bold","italic":"Courier-Oblique","scientific":"Courier-BoldOblique"}
}
DEFAULT_FAMILY = "Helvetica"

US_STATES = {
    "AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado",
    "CT":"Connecticut","DE":"Delaware","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho",
    "IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana",
    "ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi",
    "MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey",
    "NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma",
    "OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota",
    "TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington",
    "WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming","DC":"District of Columbia"
}
STATE_LOOKUP = {k.lower():v for k,v in US_STATES.items()}
STATE_LOOKUP.update({v.lower():v for v in US_STATES.values()})

# include, prefix, suffix, separator, format, newline, blank lines, wrap width,
# font family, font size, word spacing
DEFAULTS = {
    "scientificName":(True,"",""," ","scientific",False,0,None,"Helvetica",None,1.0),
    "scientificNameAuthorship":(True,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "identifiedBy":(True,"det. ",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "dateIdentified":(False,"",""," ","date",True,0,None,"Helvetica",None,1.0),
    "sex":(True,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "verbatimLocality":(False,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "locality":(True,"","",", ","normal",True,0,None,"Helvetica",None,1.0),
    "municipality":(True,"","",", ","normal",False,0,None,"Helvetica",None,1.0),
    "county":(True,"","",", ","normal",False,0,None,"Helvetica",None,1.0),
    "stateProvince":(True,"","",", ","bold",False,0,None,"Helvetica",None,1.0),
    "country":(True,"",""," ","bold",True,0,None,"Helvetica",None,1.0),
    "verbatimCoordinates":(False,"","",", ","normal",True,0,None,"Helvetica",None,1.0),
    "decimalLatitude":(True,"","",", ","normal",False,0,None,"Helvetica",None,1.0),
    "decimalLongitude":(True,"","",", ","normal",True,0,None,"Helvetica",None,1.0),
    "verbatimElevation":(True,"elev. ",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "minimumElevationInMeters":(False,"elev. "," m","–","normal",False,0,None,"Helvetica",None,1.0),
    "maximumElevationInMeters":(False,""," m"," ","normal",True,0,None,"Helvetica",None,1.0),
    "verbatimEventDate":(False,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "eventDate":(True,"","","    ","date",False,0,None,"Helvetica",None,1.0),
    "habitat":(True,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "recordedBy":(True,"coll. ","","    ","normal",False,0,None,"Helvetica",None,1.0),
    "fieldNumber":(True,"field no. ",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "recordNumber":(False,"record no. ",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "occurrenceRemarks":(False,"",""," ","normal",True,0,None,"Helvetica",None,1.0),
    "eventRemarks":(False,"",""," ","normal",True,0,None,"Helvetica",None,1.0)
}
EXCLUDE = {"catalogNumber","occurrenceID","institutionCode","collectionCode","basisOfRecord","datasetKey","gbifID","id"}
IDENTIFICATION_FIELDS = ["scientificName","scientificNameAuthorship","identifiedBy","dateIdentified"]

def clean(v):
    if v is None or pd.isna(v): return ""
    v = str(v).strip()
    return "" if v.lower() in {"nan","none","null"} else v

def state_name(v):
    v = clean(v)
    if not v: return None
    if v.lower() in STATE_LOOKUP: return STATE_LOOKUP[v.lower()]
    return STATE_LOOKUP.get(re.split(r"[,;/]",v)[0].strip().lower())

def pretty_date(v):
    v = clean(v)
    if not v or "/" in v: return v
    try:
        d = pd.to_datetime(v, errors="raise")
        return f"{d.day} {d.strftime('%b %Y')}"
    except Exception:
        return v

def sex_symbol(v):
    v = clean(v).lower()
    if not v: return ""
    if "♀" in v or v in {"female","f","1 female","1f"} or re.search(r"\bfemale\b",v): return "♀"
    if "♂" in v or v in {"male","m","1 male","1m"} or re.search(r"\bmale\b",v): return "♂"
    return ""

def coordinates(row):
    out = []
    for field,pos,neg in (("decimalLatitude","N","S"),("decimalLongitude","E","W")):
        v = clean(row.get(field,""))
        if v:
            try:
                n = float(v)
                out.append(f"{abs(n):.6f}°{pos if n >= 0 else neg}")
            except Exception:
                out.append(v)
    return ", ".join(out)

def font_name(family, fmt):
    family = family if family in FONT_FAMILIES else DEFAULT_FAMILY
    if fmt == "date": fmt = "normal"
    return FONT_FAMILIES[family].get(fmt,FONT_FAMILIES[family]["normal"])

def value_for(field,row,cfg):
    if field == "country":
        v = clean(row.get(field,""))
        return v or ("USA" if state_name(row.get("stateProvince","")) else "")
    v = clean(row.get(field,""))
    return pretty_date(v) if cfg["format"] == "date" else v

def display_separator(s):
    return "∅" if s == "" else s.replace("\t","⇥").replace(" ","·")

def default_setting(field):
    vals = DEFAULTS.get(field,(field not in EXCLUDE,"",""," ","normal",True,0,None,"Helvetica",None,1.0))
    keys = ("include","prefix","suffix","separator","format","newline","blank_lines","wrap_width","font_family","font_size","word_spacing")
    c = dict(zip(keys,vals))
    if field in EXCLUDE: c["include"] = False
    if field == "habitat": c["prefix"] = ""
    if field in {"stateProvince","country"}: c["format"] = "bold"
    return c

def spaced_width(text,font,size,spacing=1.0):
    w = stringWidth(text,font,size)
    return w if spacing == 1 or " " not in text else w + text.count(" ")*stringWidth(" ",font,size)*(spacing-1)

def draw_spaced_text(c,text,x,y,font,size,spacing):
    if spacing == 1 or " " not in text:
        c.setFont(font,size); c.drawString(x,y,text)
        return spaced_width(text,font,size,spacing)
    start = x
    sw = stringWidth(" ",font,size)
    for part in re.split(r"( +)",text):
        if not part: continue
        if part.isspace(): x += len(part)*sw*spacing
        else:
            c.setFont(font,size); c.drawString(x,y,part); x += stringWidth(part,font,size)
    return x-start

def active_items(row,settings):
    out, coord_done = [], False
    for field,cfg in settings.items():
        if not cfg["include"] or field == "sex": continue
        if field in {"decimalLatitude","decimalLongitude"}:
            if coord_done: continue
            coord_done = True
            v = coordinates(row)
            if not v: continue
            control = "decimalLongitude" if settings.get("decimalLongitude",{}).get("include") else "decimalLatitude"
            c = settings[control]
            out.append({"field":"__coordinates__","value":v,"prefix":"","suffix":"","separator":c["separator"],
                        "newline":c["newline"],"blank_lines":c["blank_lines"],"wrap_width":c["wrap_width"],
                        "format":"normal","font_family":c["font_family"],"font_size":c["font_size"],
                        "word_spacing":c["word_spacing"]})
            continue
        v = value_for(field,row,cfg)
        if not v: continue
        out.append({"field":field,"value":v,"prefix":"" if field=="habitat" else cfg["prefix"],
                    "suffix":cfg["suffix"],"separator":cfg["separator"],"newline":cfg["newline"],
                    "blank_lines":cfg["blank_lines"],"wrap_width":cfg["wrap_width"],
                    "format":"bold" if field in {"stateProvince","country"} else cfg["format"],
                    "font_family":cfg["font_family"],"font_size":cfg["font_size"],
                    "word_spacing":cfg["word_spacing"]})
    return out

def build_lines(row,settings):
    """Identification block is always first, followed by exactly one blank line."""
    items = active_items(row,settings)
    ids = [x for x in items if x["field"] in IDENTIFICATION_FIELDS]
    ids.sort(key=lambda x: IDENTIFICATION_FIELDS.index(x["field"]))
    others = [x for x in items if x["field"] not in IDENTIFICATION_FIELDS]
    items = ids + others

    lines, current, current_wrap = [], [], None

    def finish(blank=0):
        nonlocal current,current_wrap
        if current:
            lines.append({"segments":current,"blank_after":blank,"wrap_width":current_wrap})
            current,current_wrap = [],None

    for i,item in enumerate(items):
        family,fmt,size,spacing = item["font_family"],item["format"],item["font_size"],item["word_spacing"]
        normal = font_name(family,"normal")
        if item["wrap_width"] is not None:
            current_wrap = item["wrap_width"] if current_wrap is None else min(current_wrap,item["wrap_width"])
        if item["prefix"]:
            current.append({"text":item["prefix"],"font":normal,"size":size,"spacing":spacing})
        current.append({"text":item["value"],"font":font_name(family,fmt),"size":size,"spacing":spacing})
        if item["suffix"]:
            current.append({"text":item["suffix"],"font":normal,"size":size,"spacing":spacing})

        next_item = items[i+1] if i+1 < len(items) else None
        is_id = item["field"] in IDENTIFICATION_FIELDS
        next_is_id = next_item is not None and next_item["field"] in IDENTIFICATION_FIELDS

        # Identification fields retain their configured internal line breaks,
        # but the end of the identification block always receives one blank line.
        if is_id and not next_is_id:
            finish(1)
        elif item["newline"]:
            finish(item["blank_lines"])
        elif next_item is not None:
            current.append({"text":item["separator"],"font":normal,"size":size,"spacing":spacing})

    finish()
    return lines

def segment_tokens(segment):
    out = []
    for p in re.split(r"(\s+)",segment["text"]):
        if p:
            t = dict(segment); t["text"] = p; out.append(t)
    return out

def token_size(token,auto):
    return token["size"] if token["size"] is not None else auto

def token_width(token,auto):
    return spaced_width(token["text"],token["font"],token_size(token,auto),token["spacing"])

def wrap_segments(segments,auto,width):
    tokens = []
    for s in segments: tokens.extend(segment_tokens(s))
    lines,current,w = [],[],0
    for token in tokens:
        tw = token_width(token,auto)
        if current and w+tw > width and token["text"].strip():
            lines.append(current); current=[]; w=0
            token = dict(token); token["text"] = token["text"].lstrip()
            if not token["text"]: continue
            tw = token_width(token,auto)
        current.append(token); w += tw
    if current: lines.append(current)
    return lines

def line_height(tokens,auto):
    return max((token_size(t,auto) for t in tokens),default=auto)

def render_plan(lines,auto):
    full, top = LABEL_W-2*PAD_X, LABEL_W-2*PAD_X-.45*inch
    out, rendered = [],0
    for logical in lines:
        width = logical["wrap_width"]*inch if logical["wrap_width"] is not None else full
        width = min(width, top if rendered < 2 else full)
        wrapped = wrap_segments(logical["segments"],auto,width)
        last_h = auto
        for line in wrapped:
            last_h = line_height(line,auto)
            out.append({"tokens":line,"height":last_h}); rendered += 1
        out.extend({"tokens":None,"height":last_h} for _ in range(logical["blank_after"]))
    return out

def best_size(lines):
    for n in range(int(DEFAULT_SIZE*4),int(MIN_SIZE*4)-1,-1):
        s = n/4
        if sum(x["height"]*LINE_SPACING for x in render_plan(lines,s)) <= LABEL_H-PAD_TOP-PAD_BOTTOM:
            return s
    return MIN_SIZE

def draw_token_line(c,tokens,x,y,auto):
    for t in tokens:
        size = token_size(t,auto)
        x += draw_spaced_text(c,t["text"],x,y,t["font"],size,t["spacing"])

def draw_label(c,x,y,row,settings,border=False):
    c.saveState(); c.translate(x,y); c.translate(0,LABEL_W); c.rotate(-90)
    if border: c.setLineWidth(.3); c.rect(0,0,LABEL_W,LABEL_H)
    logical = build_lines(row,settings)
    auto = best_size(logical)
    p = render_plan(logical,auto)
    yy = LABEL_H-PAD_TOP
    for item in p:
        h = item["height"]
        if item["tokens"] is not None:
            draw_token_line(c,item["tokens"],PAD_X,yy-h,auto)
        yy -= h*LINE_SPACING

    if settings.get("sex",{}).get("include"):
        symbol = sex_symbol(row.get("sex",""))
        if symbol:
            cfg = settings["sex"]
            family = cfg.get("font_family","Helvetica")
            f = font_name(family,"normal")
            size = cfg.get("font_size") or 15
            c.setFont(f,size)
            c.drawRightString(LABEL_W-PAD_X,LABEL_H-PAD_TOP-size,symbol)
    c.restoreState()

def page_positions():
    # Four rotated 3 x 5 inch footprints arranged as one contiguous
    # 6 x 10 inch block centered on Letter paper. The two columns share
    # their center vertical edge and the two rows share their center
    # horizontal edge, reducing the number of cuts needed.
    fw, fh = LABEL_H, LABEL_W
    left = (PAGE_W - 2*fw) / 2
    bottom = (PAGE_H - 2*fh) / 2
    return [
        (left, bottom + fh),       # upper left
        (left + fw, bottom + fh),  # upper right
        (left, bottom),            # lower left
        (left + fw, bottom)        # lower right
    ]

def create_pdf(df,settings,path,border=False):
    c = canvas.Canvas(path,pagesize=letter)
    pos = page_positions()
    for i,(_,row) in enumerate(df.iterrows()):
        if i and i%4 == 0: c.showPage()
        draw_label(c,*pos[i%4],row,settings,border)
    c.save()

class LabelPreview(tk.Canvas):
    def __init__(self,parent,**kwargs):
        super().__init__(parent,background="#d8d8d8",highlightthickness=0,**kwargs)
        self.row=self.settings=None
        self.bind("<Configure>",lambda e:self.redraw())

    def set_label(self,row,settings):
        self.row,self.settings=row,settings
        self.redraw()

    def redraw(self):
        self.delete("all")
        if self.row is None:
            self.create_text(max(self.winfo_width()/2,1),max(self.winfo_height()/2,1),
                             text="Load a CSV to preview a label.",fill="#555")
            return
        cw,ch=self.winfo_width(),self.winfo_height()
        if cw<50 or ch<50:return
        scale=max(1,min((cw-40)/5,(ch-40)/3))
        w,h=5*scale,3*scale
        x0,y0=(cw-w)/2,(ch-h)/2
        self.create_rectangle(x0,y0,x0+w,y0+h,fill="white",outline="#555")
        logical=build_lines(self.row,self.settings)
        auto=best_size(logical); p=render_plan(logical,auto)
        # scale is preview pixels per physical inch. ReportLab dimensions
        # are points, so convert points to preview pixels with scale/72.
        pt_to_px=scale/72.0
        yy=y0+PAD_TOP*pt_to_px
        for item in p:
            hpt=item["height"]
            if item["tokens"] is not None:
                xx=x0+PAD_X*pt_to_px
                for t in item["tokens"]:
                    size=token_size(t,auto); px=max(6,int(round(size*pt_to_px))); f=t["font"]
                    fam="Times" if f.startswith("Times") else "Courier" if f.startswith("Courier") else "Helvetica"
                    weight="bold" if "Bold" in f else "normal"
                    slant="italic" if ("Italic" in f or "Oblique" in f) else "roman"
                    text=t["text"]
                    if text.isspace():
                        xx += len(text)*px*.33*t["spacing"]
                    else:
                        # Tk's named color "white" can be inherited on some macOS
                        # configurations, so force preview label text to black.
                        obj=self.create_text(xx,yy,text=text,anchor="nw",
                                             font=(fam,px,weight,slant),fill="black")
                        box=self.bbox(obj)
                        if box: xx=box[2]
            yy += hpt*pt_to_px*LINE_SPACING

        if self.settings.get("sex",{}).get("include"):
            s=sex_symbol(self.row.get("sex",""))
            if s:
                cfg=self.settings["sex"]; fam=cfg.get("font_family","Helvetica")
                size=cfg.get("font_size") or 15
                self.create_text(x0+w-PAD_X*pt_to_px,y0+PAD_TOP*pt_to_px,text=s,anchor="ne",
                                 font=(fam,max(10,int(round(size*pt_to_px)))),fill="black")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Darwin Core Odonata Label Generator")
        self.geometry("1500x850"); self.minsize(1100,650)
        self.df=self.path=None; self.settings={}; self.preview_index=0; self.drag_item=None
        self.build()

    def build(self):
        top=ttk.Frame(self,padding=8); top.pack(fill="x")
        ttk.Button(top,text="Open Darwin Core CSV",command=self.open_csv).pack(side="left")
        ttk.Separator(top,orient="vertical").pack(side="left",fill="y",padx=8)
        ttk.Button(top,text="Load Template",command=self.load_template).pack(side="left",padx=2)
        ttk.Button(top,text="Save Template",command=self.save_template).pack(side="left",padx=2)
        self.file_label=ttk.Label(top,text="No CSV loaded"); self.file_label.pack(side="left",padx=12)

        paned=ttk.Panedwindow(self,orient="horizontal"); paned.pack(fill="both",expand=True,padx=8,pady=(0,8))
        left,right=ttk.Frame(paned),ttk.Frame(paned); paned.add(left,weight=3); paned.add(right,weight=2)

        toolbar=ttk.Frame(left); toolbar.pack(fill="x",pady=(0,5))
        for text_,cmd in [
            ("Include Selected",lambda:self.bulk_include(True)),
            ("Exclude Selected",lambda:self.bulk_include(False)),
            ("Select Included",self.select_included),
            ("Select All",self.select_all),
            ("Clear Selection",lambda:self.tree.selection_remove(self.tree.selection()))
        ]:
            ttk.Button(toolbar,text=text_,command=cmd).pack(side="left",padx=2)

        cols=("on","field","prefix","suffix","separator","newline","blank","wrap","font","size","spacing","format")
        heads={"on":"Use","field":"Field","prefix":"Prefix","suffix":"Suffix","separator":"Separator",
               "newline":"New line","blank":"Blank","wrap":"Wrap","font":"Font","size":"Size",
               "spacing":"Word space","format":"Format"}
        widths={"on":40,"field":185,"prefix":80,"suffix":70,"separator":70,"newline":65,"blank":45,
                "wrap":60,"font":75,"size":50,"spacing":70,"format":75}
        tf=ttk.Frame(left); tf.pack(fill="both",expand=True)
        self.tree=ttk.Treeview(tf,columns=cols,show="headings",selectmode="extended")
        for col in cols:
            self.tree.heading(col,text=heads[col]); self.tree.column(col,width=widths[col],anchor="w" if col=="field" else "center")
        sy=ttk.Scrollbar(tf,orient="vertical",command=self.tree.yview)
        sx=ttk.Scrollbar(tf,orient="horizontal",command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
        self.tree.grid(row=0,column=0,sticky="nsew"); sy.grid(row=0,column=1,sticky="ns"); sx.grid(row=1,column=0,sticky="ew")
        tf.rowconfigure(0,weight=1); tf.columnconfigure(0,weight=1)
        self.tree.bind("<Double-1>",self.double_click)
        self.tree.bind("<ButtonPress-1>",self.drag_start)
        self.tree.bind("<B1-Motion>",self.drag_motion)
        self.tree.bind("<ButtonRelease-1>",self.drag_end)

        ttk.Label(right,text="Label Preview",font=("TkDefaultFont",11,"bold")).pack(anchor="w")
        self.preview=LabelPreview(right,height=400); self.preview.pack(fill="both",expand=True,pady=5)
        nav=ttk.Frame(right); nav.pack(fill="x")
        ttk.Button(nav,text="◀ Previous",command=lambda:self.change_preview(-1)).pack(side="left")
        ttk.Button(nav,text="Next ▶",command=lambda:self.change_preview(1)).pack(side="right")
        mid=ttk.Frame(nav); mid.pack()
        ttk.Label(mid,text="Record").pack(side="left")
        self.record_var=tk.StringVar(value="1")
        ent=ttk.Entry(mid,textvariable=self.record_var,width=7); ent.pack(side="left",padx=3)
        ent.bind("<Return>",lambda e:self.goto_record())
        self.record_total=ttk.Label(mid,text="/ 0"); self.record_total.pack(side="left")
        ttk.Label(right,justify="left",text=(
            "The identification section is always first:\n"
            "scientificName → scientificNameAuthorship → identifiedBy → dateIdentified\n"
            "and is always followed by one blank line.\n\n"
            "Drag fields to reorder the remaining data. Double-click a field to edit it.\n"
            "Font size: blank = Auto. Word spacing: 1.0 = normal.\n"
            "Wrap: maximum line width in inches; blank = Auto."
        )).pack(anchor="w",pady=8)

        bottom=ttk.Frame(self,padding=8); bottom.pack(fill="x")
        self.border=tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom,text="Show cutting borders",variable=self.border).pack(side="left")
        ttk.Button(bottom,text="Generate PDF",command=self.generate).pack(side="right",ipadx=15,ipady=5)

    def row_values(self,field):
        c=self.settings[field]
        return ("✓" if c["include"] else "",field,c["prefix"],c["suffix"],display_separator(c["separator"]),
                "↵" if c["newline"] else "",c["blank_lines"],
                "Auto" if c["wrap_width"] is None else f'{c["wrap_width"]:g}"',
                c["font_family"],"Auto" if c["font_size"] is None else f'{c["font_size"]:g}',
                f'{c["word_spacing"]:g}',c["format"])

    def refresh(self,field):
        self.tree.item(field,values=self.row_values(field))

    def open_csv(self):
        path=filedialog.askopenfilename(title="Select Darwin Core CSV",filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path:return
        try:
            try: df=pd.read_csv(path,dtype=str,keep_default_na=False)
            except UnicodeDecodeError: df=pd.read_csv(path,dtype=str,keep_default_na=False,encoding="latin1")
        except Exception as e:
            messagebox.showerror("CSV Error",str(e)); return
        if df.empty:
            messagebox.showwarning("Empty CSV","The CSV contains no records."); return
        self.df,self.path,self.preview_index=df,path,0
        self.file_label.config(text=f"{os.path.basename(path)} — {len(df):,} occurrences")
        self.record_total.config(text=f"/ {len(df):,}"); self.record_var.set("1")
        self.load_fields(); self.update_preview()

    def load_fields(self):
        self.tree.delete(*self.tree.get_children()); self.settings={}
        columns=list(self.df.columns)
        order=[f for f in IDENTIFICATION_FIELDS if f in columns]
        order += [f for f in DEFAULTS if f in columns and f not in order]
        order += [f for f in columns if f not in order]
        for field in order:
            self.settings[field]=default_setting(field)
            self.tree.insert("","end",iid=field,values=self.row_values(field))

    def bulk_include(self,enabled):
        for field in self.tree.selection():
            self.settings[field]["include"]=enabled; self.refresh(field)
        self.update_preview()

    def select_all(self):
        self.tree.selection_set(self.tree.get_children())

    def select_included(self):
        self.tree.selection_remove(self.tree.selection())
        selected=[f for f in self.tree.get_children() if self.settings[f]["include"]]
        if selected:self.tree.selection_set(selected)

    def drag_start(self,event):
        self.drag_item=self.tree.identify_row(event.y) if self.tree.identify_region(event.x,event.y)=="cell" else None

    def drag_motion(self,event):
        if not self.drag_item:return
        target=self.tree.identify_row(event.y)
        if target and target!=self.drag_item:
            children=list(self.tree.get_children())
            self.tree.move(self.drag_item,"",children.index(target))

    def drag_end(self,event):
        if self.drag_item:self.drag_item=None; self.update_preview()

    def double_click(self,event):
        field=self.tree.identify_row(event.y)
        if field:self.edit_field(field)

    def edit_field(self,field):
        c=self.settings[field]
        w=tk.Toplevel(self); w.title(f"Edit field — {field}"); w.transient(self); w.grab_set(); w.resizable(False,False)
        f=ttk.Frame(w,padding=15); f.pack()
        ttk.Label(f,text=field,font=("TkDefaultFont",11,"bold")).grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,10))

        use=tk.BooleanVar(value=c["include"]); newline=tk.BooleanVar(value=c["newline"])
        prefix=tk.StringVar(value=c["prefix"]); suffix=tk.StringVar(value=c["suffix"])
        separator=tk.StringVar(value=c["separator"]); blank=tk.IntVar(value=c["blank_lines"])
        wrap=tk.StringVar(value="" if c["wrap_width"] is None else str(c["wrap_width"]))
        family=tk.StringVar(value=c["font_family"]); size=tk.StringVar(value="" if c["font_size"] is None else str(c["font_size"]))
        spacing=tk.StringVar(value=str(c["word_spacing"])); fmt=tk.StringVar(value=c["format"])

        ttk.Checkbutton(f,text="Include field",variable=use).grid(row=1,column=0,columnspan=2,sticky="w")
        ttk.Checkbutton(f,text="Start a new line after this field",variable=newline).grid(row=2,column=0,columnspan=2,sticky="w",pady=(3,10))

        def add_entry(row,label,var,width=32):
            ttk.Label(f,text=label).grid(row=row,column=0,sticky="e",padx=5,pady=4)
            e=ttk.Entry(f,textvariable=var,width=width); e.grid(row=row,column=1,sticky="w"); return e

        pe=add_entry(3,"Prefix:",prefix)
        if field=="habitat": prefix.set(""); pe.configure(state="disabled")
        add_entry(4,"Suffix:",suffix)
        add_entry(5,"Separator after:",separator)

        ttk.Label(f,text="Blank lines after:").grid(row=6,column=0,sticky="e",padx=5,pady=4)
        ttk.Spinbox(f,from_=0,to=10,textvariable=blank,width=7).grid(row=6,column=1,sticky="w")

        ttk.Label(f,text="Wrap width:").grid(row=7,column=0,sticky="e",padx=5,pady=4)
        wf=ttk.Frame(f); wf.grid(row=7,column=1,sticky="w")
        ttk.Entry(wf,textvariable=wrap,width=10).pack(side="left"); ttk.Label(wf,text=' inches (blank = Auto)').pack(side="left")

        ttk.Separator(f,orient="horizontal").grid(row=8,column=0,columnspan=2,sticky="ew",pady=10)
        ttk.Label(f,text="Typography",font=("TkDefaultFont",10,"bold")).grid(row=9,column=0,columnspan=2,sticky="w")

        ttk.Label(f,text="Font:").grid(row=10,column=0,sticky="e",padx=5,pady=4)
        ttk.Combobox(f,textvariable=family,values=list(FONT_FAMILIES),state="readonly",width=29).grid(row=10,column=1,sticky="w")

        ttk.Label(f,text="Font size:").grid(row=11,column=0,sticky="e",padx=5,pady=4)
        sf=ttk.Frame(f); sf.grid(row=11,column=1,sticky="w")
        ttk.Entry(sf,textvariable=size,width=10).pack(side="left"); ttk.Label(sf,text=" pt (blank = Auto)").pack(side="left")

        ttk.Label(f,text="Word spacing:").grid(row=12,column=0,sticky="e",padx=5,pady=4)
        spf=ttk.Frame(f); spf.grid(row=12,column=1,sticky="w")
        ttk.Entry(spf,textvariable=spacing,width=10).pack(side="left"); ttk.Label(spf,text=" × normal").pack(side="left")

        ttk.Label(f,text="Formatting:").grid(row=13,column=0,sticky="e",padx=5,pady=4)
        cb=ttk.Combobox(f,textvariable=fmt,state="readonly",values=["normal","bold","italic","scientific","date"],width=29)
        cb.grid(row=13,column=1,sticky="w")
        if field in {"stateProvince","country"}: fmt.set("bold"); cb.configure(state="disabled")

        if field in IDENTIFICATION_FIELDS:
            ttk.Label(f,text="This field is part of the fixed identification section at the top.",
                      foreground="#555").grid(row=14,column=0,columnspan=2,sticky="w",pady=(7,0))
        elif field=="sex":
            ttk.Label(f,text="sex is displayed as ♂ or ♀ in the upper-right corner.",
                      foreground="#555").grid(row=14,column=0,columnspan=2,sticky="w",pady=(7,0))

        def save():
            try:
                b=int(blank.get())
                if b<0:raise ValueError
            except Exception:
                messagebox.showerror("Invalid Blank Lines","Blank lines must be 0 or greater.",parent=w); return
            try:
                ww=None if not wrap.get().strip() else float(wrap.get())
                if ww is not None and not .5<=ww<=4.7:raise ValueError
            except Exception:
                messagebox.showerror("Invalid Wrap Width","Use 0.5–4.7 inches, or blank for Auto.",parent=w); return
            try:
                sz=None if not size.get().strip() else float(size.get())
                if sz is not None and not 4<=sz<=30:raise ValueError
            except Exception:
                messagebox.showerror("Invalid Font Size","Use 4–30 points, or blank for Auto.",parent=w); return
            try:
                ws=float(spacing.get())
                if not .1<=ws<=5:raise ValueError
            except Exception:
                messagebox.showerror("Invalid Word Spacing","Use a value from 0.1 to 5.0.",parent=w); return

            c.update(include=use.get(),newline=newline.get(),blank_lines=b,wrap_width=ww,
                     prefix="" if field=="habitat" else prefix.get().lower(),
                     suffix=suffix.get(),separator=separator.get(),font_family=family.get(),
                     font_size=sz,word_spacing=ws,
                     format="bold" if field in {"stateProvince","country"} else fmt.get())
            self.refresh(field); self.update_preview(); w.destroy()

        ttk.Button(f,text="Save",command=save).grid(row=15,column=0,columnspan=2,pady=(15,0))

    def ordered_settings(self):
        # The tree may visually be reordered, but the identification fields
        # are always forced to the top for label generation and templates.
        order=list(self.tree.get_children())
        order=[f for f in IDENTIFICATION_FIELDS if f in order]+[f for f in order if f not in IDENTIFICATION_FIELDS]
        return {f:self.settings[f] for f in order}

    def update_preview(self):
        if self.df is None:return
        self.preview_index=max(0,min(self.preview_index,len(self.df)-1))
        self.record_var.set(str(self.preview_index+1))
        self.preview.set_label(self.df.iloc[self.preview_index],self.ordered_settings())

    def change_preview(self,n):
        if self.df is None:return
        self.preview_index=(self.preview_index+n)%len(self.df); self.update_preview()

    def goto_record(self):
        if self.df is None:return
        try:
            n=int(self.record_var.get())
            if not 1<=n<=len(self.df):raise ValueError
            self.preview_index=n-1; self.update_preview()
        except ValueError:
            messagebox.showwarning("Invalid Record",f"Enter a record number from 1 to {len(self.df)}.")

    def save_template(self):
        if not self.settings:
            messagebox.showwarning("No Formatting","Load a CSV before saving a template."); return
        path=filedialog.asksaveasfilename(title="Save Label Template",defaultextension=".json",
                                          initialfile="odonata_label_template.json",
                                          filetypes=[("Label template","*.json"),("JSON files","*.json")])
        if not path:return
        ordered=self.ordered_settings()
        template={"templateType":"Darwin Core Odonata Label Template","version":4,
                  "fieldOrder":list(ordered),"fields":{f:dict(ordered[f]) for f in ordered},
                  "showCuttingBorders":self.border.get()}
        try:
            with open(path,"w",encoding="utf-8") as fh:json.dump(template,fh,indent=2,ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Template Error",str(e)); return
        messagebox.showinfo("Template Saved",f"Template saved successfully.\n\n{path}")

    def load_template(self):
        if self.df is None:
            messagebox.showwarning("Load CSV First","Load a Darwin Core CSV before applying a template."); return
        path=filedialog.askopenfilename(title="Load Label Template",
                                        filetypes=[("Label template","*.json"),("JSON files","*.json"),("All files","*.*")])
        if not path:return
        try:
            with open(path,"r",encoding="utf-8") as fh:template=json.load(fh)
            fields=template["fields"]
            saved_order=template.get("fieldOrder",template.get("order",list(fields)))
        except Exception as e:
            messagebox.showerror("Template Error",f"Could not read this template:\n\n{e}"); return

        csv_fields=list(self.df.columns)
        saved_order=[f for f in IDENTIFICATION_FIELDS if f in csv_fields]+[f for f in saved_order if f not in IDENTIFICATION_FIELDS]
        new={}
        aliases={"blank":"blank_lines","wrap":"wrap_width"}

        for field in saved_order:
            if field not in csv_fields or field in new:continue
            cfg=default_setting(field)
            for old_key,val in fields.get(field,{}).items():
                key=aliases.get(old_key,old_key)
                if key in cfg:cfg[key]=val
            if field=="habitat":cfg["prefix"]=""
            if field in {"stateProvince","country"}:cfg["format"]="bold"
            cfg["prefix"]=str(cfg["prefix"]).lower()
            new[field]=cfg

        for field in csv_fields:
            if field not in new:
                cfg=default_setting(field)
                if field not in fields:cfg["include"]=False
                new[field]=cfg

        self.settings=new
        self.tree.delete(*self.tree.get_children())
        for field in new:self.tree.insert("","end",iid=field,values=self.row_values(field))
        self.border.set(bool(template.get("showCuttingBorders",template.get("border",False))))
        self.update_preview()

    def generate(self):
        if self.df is None:
            messagebox.showwarning("No Data","Load a Darwin Core CSV first."); return
        base=os.path.splitext(os.path.basename(self.path))[0]
        path=filedialog.asksaveasfilename(title="Save Labels",defaultextension=".pdf",
                                          initialfile=base+"_labels.pdf",filetypes=[("PDF files","*.pdf")])
        if not path:return
        try:create_pdf(self.df,self.ordered_settings(),path,self.border.get())
        except Exception as e:
            messagebox.showerror("PDF Error",str(e)); return
        messagebox.showinfo("Complete",f"Created {len(self.df):,} labels.\n\n{path}")

if __name__ == "__main__":
    App().mainloop()
