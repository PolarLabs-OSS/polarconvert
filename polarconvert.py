"""PolarConvert — local CSV/JSON/YAML/XML converter."""
import csv
import io
import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import yaml
from defusedxml import ElementTree as SafeET
from xml.etree import ElementTree as ET

FORMATS=("JSON","CSV","YAML","XML")
BG="#091623";PANEL="#122537";FG="#EAF6FA";ACC="#27D6D0";MUTED="#9BB5C2"

def parse_csv(text):
    reader=csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:raise ValueError("CSV senza intestazioni")
    if any(x is None or x=="" for x in reader.fieldnames):raise ValueError("Intestazioni CSV vuote")
    return list(reader)

def parse_xml(text):
    root=SafeET.fromstring(text)
    def unpack(node):
        children=list(node)
        if not children:
            return node.text.strip() if node.text and node.text.strip() else ""
        result={}
        for child in children:
            value=unpack(child)
            if child.tag in result:
                if not isinstance(result[child.tag],list):result[child.tag]=[result[child.tag]]
                result[child.tag].append(value)
            else:result[child.tag]=value
        return result
    return {root.tag:unpack(root)}

def parse(text,fmt):
    if fmt=="JSON":return json.loads(text)
    if fmt=="YAML":return yaml.safe_load(text)
    if fmt=="CSV":return parse_csv(text)
    if fmt=="XML":return parse_xml(text)
    raise ValueError("Formato non supportato")

def xml_name(name):
    import re
    s=re.sub(r"[^a-zA-Z0-9_.-]","_",str(name))
    if not s or not(s[0].isalpha() or s[0]=="_"):s="field_"+s
    return s

def write_xml(data):
    root=ET.Element("root")
    def append(parent,value):
        if isinstance(value,dict):
            for k,v in value.items():
                tag=xml_name(k)
                if isinstance(v,list):
                    for x in v:append(ET.SubElement(parent,tag),x)
                else:append(ET.SubElement(parent,tag),v)
        elif isinstance(value,list):
            for x in value:append(ET.SubElement(parent,"item"),x)
        else:
            parent.text="" if value is None else str(value)
    append(root,data)
    ET.indent(root,space="  ")
    return ET.tostring(root,encoding="unicode")

def write_csv(data):
    if isinstance(data,dict):data=[data]
    if not isinstance(data,list) or not all(isinstance(x,dict) for x in data):
        raise ValueError("Per CSV servono una lista di oggetti oppure un oggetto")
    keys=list(dict.fromkeys(k for item in data for k in item))
    if not keys:raise ValueError("Nessuna colonna CSV")
    out=io.StringIO(newline="")
    writer=csv.DictWriter(out,fieldnames=keys,extrasaction="ignore")
    writer.writeheader()
    for item in data:
        writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in item.items()})
    return out.getvalue()

def serialize(data,fmt):
    if fmt=="JSON":return json.dumps(data,indent=2,ensure_ascii=False)
    if fmt=="YAML":return yaml.safe_dump(data,allow_unicode=True,sort_keys=False)
    if fmt=="CSV":return write_csv(data)
    if fmt=="XML":return write_xml(data)
    raise ValueError("Formato non supportato")

def convert(content,source,target):
    return serialize(parse(content,source),target)

class App:
    def __init__(self,root):
        self.root=root;root.title("PolarConvert | PolarLabs-OSS");root.geometry("1090x750");root.configure(bg=BG)
        frame=tk.Frame(root,bg=BG,padx=24,pady=19);frame.pack(fill="both",expand=True)
        tk.Label(frame,text="POLAR / CONVERT",bg=BG,fg=ACC,font=("Segoe UI",26,"bold")).pack(anchor="w")
        tk.Label(frame,text="Converti, valida e formatta dati in locale  •  CSV / JSON / YAML / XML",bg=BG,fg=MUTED).pack(anchor="w",pady=(0,15))
        bar=tk.Frame(frame,bg=BG);bar.pack(fill="x",pady=(0,12))
        self.source=tk.StringVar(value="JSON");self.target=tk.StringVar(value="YAML")
        tk.Label(bar,text="Da",bg=BG,fg=FG).pack(side="left")
        ttk.Combobox(bar,values=FORMATS,textvariable=self.source,width=10,state="readonly").pack(side="left",padx=(8,16))
        tk.Label(bar,text="A",bg=BG,fg=FG).pack(side="left")
        ttk.Combobox(bar,values=FORMATS,textvariable=self.target,width=10,state="readonly").pack(side="left",padx=(8,16))
        for label,func in [("Apri file",self.open),("Valida",self.validate),("Converti",self.run),("Salva output",self.save)]:
            self.button(bar,label,func,label=="Converti").pack(side="left",padx=(0,8))
        body=tk.Frame(frame,bg=BG);body.pack(fill="both",expand=True)
        for idx,title in enumerate(("INPUT","OUTPUT")):
            col=tk.Frame(body,bg=BG);col.grid(row=0,column=idx,sticky="nsew",padx=(0,9) if idx==0 else (9,0))
            tk.Label(col,text=title,fg=FG,bg=BG,font=("Segoe UI",11,"bold")).pack(anchor="w",pady=(0,8))
            area=tk.Text(col,bg=PANEL,fg=FG,insertbackground=FG,font=("Consolas",10),wrap="none",undo=True,relief="flat",padx=10,pady=10)
            area.pack(fill="both",expand=True)
            if idx==0:self.input=area
            else:self.output=area
        body.grid_columnconfigure(0,weight=1);body.grid_columnconfigure(1,weight=1);body.grid_rowconfigure(0,weight=1)
        lower=tk.Frame(frame,bg=BG);lower.pack(fill="x",pady=(12,0))
        self.button(lower,"Copia risultato",self.copy).pack(side="left",padx=(0,8))
        self.button(lower,"Formatta input",self.format_input).pack(side="left")
        self.status=tk.StringVar(value="Pronto")
        tk.Label(frame,textvariable=self.status,bg=BG,fg=MUTED).pack(anchor="w",pady=(12,0))
        tk.Label(frame,text="PolarLabs-OSS  •  Nessun cloud  •  XML in forma gerarchica semplificata",bg=BG,fg=MUTED,font=("Segoe UI",8)).pack(anchor="w",pady=6)
    def button(self,frame,title,fun,primary=False):
        return tk.Button(frame,text=title,command=fun,bg=ACC if primary else PANEL,fg=BG if primary else FG,relief="flat",padx=12,pady=8)
    def content(self):return self.input.get("1.0","end-1c")
    def open(self):
        p=filedialog.askopenfilename(filetypes=[("Dati","*.json *.csv *.yaml *.yml *.xml"),("Tutti","*.*")])
        if not p:return
        try:
            s=Path(p).read_text(encoding="utf-8-sig")
            self.input.delete("1.0","end");self.input.insert("1.0",s)
            ext=Path(p).suffix.lower()
            fmt={".json":"JSON",".csv":"CSV",".yaml":"YAML",".yml":"YAML",".xml":"XML"}.get(ext)
            if fmt:self.source.set(fmt)
            self.status.set("File caricato: "+Path(p).name)
        except Exception as e:messagebox.showerror("PolarConvert",str(e))
    def validate(self):
        try:
            data=parse(self.content(),self.source.get())
            self.status.set("Valido • Tipo: "+type(data).__name__)
        except Exception as e:self.status.set("Non valido: "+str(e));messagebox.showerror("Validazione",str(e))
    def run(self):
        try:
            value=convert(self.content(),self.source.get(),self.target.get())
            self.output.delete("1.0","end");self.output.insert("1.0",value)
            self.status.set(f"Conversione {self.source.get()} → {self.target.get()} completata")
        except Exception as e:self.status.set("Errore: "+str(e));messagebox.showerror("PolarConvert",str(e))
    def format_input(self):
        try:
            value=serialize(parse(self.content(),self.source.get()),self.source.get())
            self.input.delete("1.0","end");self.input.insert("1.0",value)
            self.status.set("Input formattato")
        except Exception as e:messagebox.showerror("PolarConvert",str(e))
    def save(self):
        text=self.output.get("1.0","end-1c")
        if not text:return
        ext={"JSON":".json","YAML":".yaml","CSV":".csv","XML":".xml"}[self.target.get()]
        p=filedialog.asksaveasfilename(defaultextension=ext,filetypes=[(self.target.get(),"*"+ext)])
        if p:
            try:Path(p).write_text(text,encoding="utf-8");self.status.set("Salvato: "+p)
            except OSError as e:messagebox.showerror("PolarConvert",str(e))
    def copy(self):
        text=self.output.get("1.0","end-1c")
        if text:self.root.clipboard_clear();self.root.clipboard_append(text);self.status.set("Risultato copiato")
from ui_theme import apply_theme

if __name__=="__main__":
    root=tk.Tk();App(root);apply_theme(root);root.mainloop()
