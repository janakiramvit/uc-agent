from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import tempfile, shutil

p=Path('/Users/janakirampulipati/ibd-research-review/ibd-prototype-evidence-review.xlsx')
ns='{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
ET.register_namespace('x','http://schemas.openxmlformats.org/spreadsheetml/2006/main')
tmp=Path(tempfile.mkstemp(suffix='.xlsx')[1])
with ZipFile(p,'r') as zin, ZipFile(tmp,'w',ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data=zin.read(item.filename)
        if item.filename.startswith('xl/worksheets/sheet') and item.filename.endswith('.xml'):
            root=ET.fromstring(data)
            views=root.find(ns+'sheetViews')
            if views is None:
                views=ET.Element(ns+'sheetViews'); root.insert(0,views)
            view=views.find(ns+'sheetView')
            if view is None:
                view=ET.SubElement(views,ns+'sheetView',{'showGridLines':'0','workbookViewId':'0'})
            if view.find(ns+'pane') is None:
                ET.SubElement(view,ns+'pane',{'ySplit':'4','topLeftCell':'A5','activePane':'bottomLeft','state':'frozen'})
            data=ET.tostring(root,encoding='utf-8',xml_declaration=True)
        zout.writestr(item,data)
shutil.move(tmp,p)
