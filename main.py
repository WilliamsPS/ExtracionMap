import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import datetime
from tkcalendar import Calendar
from gee import trans_shape, generando_collection, sentinel, landcover, dem, ndwi_med, ndwi_max
import os
import sys
import io
import threading

ruta = os.path.dirname(__file__)

class TextRedirector(io.TextIOBase):
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END) 
def pick_date(entry):
    def set_date():
        entry.delete(0, tk.END)
        entry.insert(0, cal.selection_get())
        top.destroy()
    top = tk.Toplevel(root)
    cal = Calendar(top, selectmode='day', year=datetime.datetime.now(
    ).year, month=datetime.datetime.now().month, day=datetime.datetime.now().day)
    cal.pack(fill="both", expand=True)
    tk.Button(top, text="Ok", command=set_date).pack()
def browse_file():
    filename = filedialog.askopenfilename()
    entry_shape_path.delete(0, tk.END)
    entry_shape_path.insert(0, filename)
def validate_entry(input):
    """Valida que la entrada sea alfanumérica y no exceda los 8 caracteres."""
    if len(input) <= 8 and (input.isalnum() or input == ""):
        return True
    else:
        return False
def hilo_process():
    thread = threading.Thread(target=process_images)
    thread.start()
def process_images():
    text_area.delete("1.0", tk.END)
    nombre_proy = nom_proy.get()
    start_date = date_start.get()
    end_date = date_end.get()
    cloud_cover = scale_cloud.get()
    shape_path = entry_shape_path.get()
    geometry = trans_shape(shape_path)
    proy_path = os.path.join(ruta,  'output', str(nombre_proy))
    if os.path.exists(proy_path) == False:
        os.makedirs(proy_path)
        text_area.insert(tk.END, f"Se ha creado la carpeta: {proy_path}\n")
    else:
        text_area.insert(tk.END, f"La carpeta {proy_path} ya existe\n")
    nom_imgSent_gui = 'Sentinel2_RGB843_' + str(nombre_proy)
    nom_imgNDWImedia_gui = 'NDWI_median_' + str(nombre_proy)
    nom_imgNDWImax_gui = 'NDWI_max_' + str(nombre_proy)
    nombre_cs_gui = 'Landcover_10m_' + str(nombre_proy)
    nombre_dem_gui = 'ALOSDSM_30m_' + str(nombre_proy)
    text_area.insert(
        tk.END, f"Proceso iniciado con los siguientes parámetros:\n")
    text_area.insert(tk.END, f"Fecha de inicio: {start_date}\n")
    text_area.insert(tk.END, f"Fecha de fin: {end_date}\n")
    text_area.insert(tk.END, f"Total de nubes: {cloud_cover}\n")
    original_stdout = sys.stdout
    sys.stdout = TextRedirector(text_area)
    try:
        collection1 = generando_collection(
            start_date, end_date, geometry, cloud_cover)
    finally:
        sys.stdout = original_stdout
    original_stdout = sys.stdout
    sys.stdout = TextRedirector(text_area)
    try:
        sentinel(collection1, geometry, nom_imgSent_gui)
    finally:
        sys.stdout = original_stdout
    if check_landcover.get():
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(text_area)
        try:
            landcover(geometry, proy_path, nombre_cs_gui)
        finally:
            sys.stdout = original_stdout
    if check_dem.get():
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(text_area)
        try:
            dem(geometry, proy_path, nombre_dem_gui)
        finally:
            sys.stdout = original_stdout
    if check_ndwi_med.get():
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(text_area)
        try:
            ndwi_med(collection1, geometry, proy_path, nom_imgNDWImedia_gui)
        finally:
            sys.stdout = original_stdout
    if check_ndwi_max.get():
        original_stdout = sys.stdout
        sys.stdout = TextRedirector(text_area)
        try:
            ndwi_max(collection1, geometry, proy_path, nom_imgNDWImax_gui)
        finally:
            sys.stdout = original_stdout
root = tk.Tk()
root.title("Procesamiento de Imágenes Satelitales")
frame_left = tk.Frame(root, padx=10, pady=10)
frame_left.grid(row=0, column=0, sticky="nw")
label_nom_proy = tk.Label(frame_left, text="Nombre del proyecto:")
label_nom_proy.pack(fill='x')
vcmd = (root.register(validate_entry), '%P')
nom_proy = tk.Entry(frame_left, validate="key", validatecommand=vcmd)
nom_proy.pack(fill='x')
date_start = tk.Entry(frame_left)
date_end = tk.Entry(frame_left)
button_start_date = tk.Button(
    frame_left, text="Seleccione fecha de inicio", command=lambda: pick_date(date_start))
button_end_date = tk.Button(
    frame_left, text="Seleccione fecha de fin", command=lambda: pick_date(date_end))
label_start_date = tk.Label(frame_left, text="Ingrese fecha de inicio:")
label_start_date.pack(fill='x')
date_start.pack(fill='x')
button_start_date.pack(fill='x')
label_end_date = tk.Label(frame_left, text="Ingrese fecha de fin:")
label_end_date.pack(fill='x')
date_end.pack(fill='x')
button_end_date.pack(fill='x')
label_cloud = tk.Label(frame_left, text="Total Nubes:")
label_cloud.pack(fill='x')
scale_cloud = tk.Scale(frame_left, from_=0, to=100, orient="horizontal")
scale_cloud.set(20)
scale_cloud.pack(fill='x')
label_shape_path = tk.Label(frame_left, text="Ruta Shape:")
label_shape_path.pack(fill='x')
entry_shape_path = tk.Entry(frame_left)
entry_shape_path.pack(fill='x')
button_browse = tk.Button(frame_left, text="Buscar", command=browse_file)
button_browse.pack(fill='x')
frame_right = tk.Frame(root, padx=10, pady=10)
frame_right.grid(row=0, column=1, sticky="ne")
check_landcover = tk.BooleanVar()
check_dem = tk.BooleanVar()
check_ndwi_med = tk.BooleanVar()
check_ndwi_max = tk.BooleanVar()
tk.Checkbutton(frame_right, text="Landcover",
               variable=check_landcover).pack(anchor='nw')
tk.Checkbutton(frame_right, text="DEM", variable=check_dem).pack(anchor='nw')
tk.Checkbutton(frame_right, text="NDWI Medio",
               variable=check_ndwi_med).pack(anchor='nw')
tk.Checkbutton(frame_right, text="NDWI Máximo",
               variable=check_ndwi_max).pack(anchor='nw')
label_output = tk.Label(frame_right, text="Mensaje de salida:")
label_output.pack(fill='x')
text_area = tk.Text(frame_right, height=10, width=50)
text_area.pack()
button_process = tk.Button(
    root, text="Procesar Imágenes", command=hilo_process)
button_process.grid(row=1, column=0, columnspan=2, pady=10)
root.mainloop()
