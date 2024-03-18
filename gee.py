import os
import time
import io
import ee
import pandas
import geemap
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

ruta = os.path.dirname(__file__)
json_file = os.path.join(ruta, 'rasterproject.json')
service_account = 'rasterproypccm@rasterprojectcom'
credentials = ee.String
ee.Initialize(credentials)

try:
    creds = Credentials.from_service_account_file(
        json_file, scopes=["https://www.googleapis.com/auth/drive"])
    service = build('drive', 'v3', credentials=creds)
    print("Autenticación exitosa.")
except Exception as e:
    print(f"Error durante la autenticación: {e}")
    exit()  
def trans_shape(shape01):
    geometry1 = geemap.shp_to_ee(shape01)
    geometry = geometry1.geometry()
    print("Transformando el shape")
    return geometry
def download_file_from_drive(file_id, file_name, destination_path):
    full_path = os.path.join(destination_path, file_name)

    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Descargado {int(status.progress() * 100)}%.")
        with open(full_path, 'wb') as f:
            f.write(fh.getvalue())
        print(f"Archivo {file_name} descargado exitosamente en {full_path}.")
    except Exception as e:
        print(f"Error al descargar el archivo: {e}")
def delete_file_from_drive(file_id):
    """Elimina un archivo de Google Drive dado su ID."""
    try:
        service.files().delete(fileId=file_id).execute()
        print(
            f"Archivo con ID {file_id} eliminado exitosamente de Google Drive.")
    except HttpError as e:
        print(f"Error al intentar eliminar el archivo con ID {file_id}: {e}")
def download_from_drive_by_description(desired_description, destination_path):
    """Descargar archivo de Google Drive basado en su descripción (nombre)."""
    try:
        results = service.files().list(
            pageSize=90, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if items:
            matching_files = [
                file for file in items if file['name'].startswith(desired_description)]
            if matching_files:
                file_to_download = matching_files[0]
                download_file_from_drive(
                    file_to_download['id'], file_to_download['name'], destination_path)
                print(
                    f"Archivo {desired_description} descargado exitosamente.")
            else:
                print(
                    f"No se encontró ningún archivo con la descripción: {desired_description}")
        else:
            print("No se encontraron archivos en el Drive.")
    except HttpError as e:
        print(f"Error al intentar listar archivos: {e}")
def export_to_drive(image, description, region, scale=10, maxPixels=10000000000000):
    start_time = time.time()
    counter = 1
    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        region=region,
        maxPixels=maxPixels
    )
    task.start()
    print(f'-Exportando archivo {description} -')
    while True:
        status = task.status()['state']
        counter += 1
        if status in ['READY', 'RUNNING']:
            if status == 'READY':
                print(
                    f"Estado de la tarea {description}: {status}, ESPERE POR FAVOR.....")
            if status == 'RUNNING' and counter % 5 == 0:
                print(
                    f'El proceso va demorando {counter//5} minutos... Trabajando')
            time.sleep(20)
        else:
            break 
    if status == 'COMPLETED':
        print(f"Archivo {description} exportado con éxito!")

    else:
        if status == 'FAILED':
            error_message = task.status().get(
                'error_message', 'No se proporcionó mensaje de error.')
            print(
                f"Error al exportar el archivo {description}. Mensaje de error: {error_message}")
        else:
            print(
                f"Error al exportar el archivo {description}. Estado final: {status}")
    time.sleep(15)
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(
        f"La funcion demoró {elapsed_time:.2f} segundos ( {int(minutes)} minutos y {seconds:.2f} segundos) en ejecutarse.")
def listar():
    try:
        results = service.files().list(
            pageSize=90, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if items:
            print(f"Se encontró {len(items)} archivo(s) en el Drive:")
            for item in items:
                print(u'{0} ({1})'.format(item['name'], item['id']))
        else:
            print("No se encontraron archivos en el Drive.")
    except HttpError as e:
        print(f"Error al intentar listar archivos: {e}")

def MascaraNubesS(image):
    qa = image.select('QA60')
    RecorteNubesMascaraS = 1 << 10
    RecorteCirrosMascaraS = 1 << 11
    MascaraS = qa.bitwiseAnd(RecorteNubesMascaraS).eq(0) \
        .And(qa.bitwiseAnd(RecorteCirrosMascaraS).eq(0))

    return image.updateMask(MascaraS)

def addNDWI(image):
    ndwi_s2 = image.expression("(green - nir) / (green + nir)", {
        'green': image.select("B3"),
        'nir': image.select("B8")
    }).rename("ndwi")
    return ndwi_s2

def generando_collection(startDate, endDate, geometry, tol_nubes):
    start_time = time.time()
    collection1 = ee.ImageCollection('COPERNICUS/S2') \
        .filterDate(startDate, endDate) \
        .filterBounds(geometry) \
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', tol_nubes)) \
        .map(MascaraNubesS)

    collection_size = collection1.size().getInfo()
    if collection_size == 0:
        print("No hay imágenes disponibles en las fechas y regiones especificadas.\n")
        exit()  
    else:
        print(f'La coleccion tiene {collection_size} imagenes')
    end_time = time.time()
    elapsed_time = end_time - start_time
    minutes, seconds = divmod(elapsed_time, 1060)
    print(
        f"La funcion demoró {elapsed_time:.2f} segundos ( {int(minutes)} minutos y {seconds:.2f} segundos) en ejecutarse.\n")
    return collection1

def sentinel(collection1, geometry, nom_imgSent='Sentinel'):
    print('EMPEZANDO EL PROCESO, APROXIMADAMENTE DURARA 60 MINUTOS. DEPENDIENDO LA DISPONIBILIDAD DE LA WEB')
    composite1 = collection1.median()
    composite1 = composite1.clip(geometry)
    image = composite1.select('B8', 'B4', 'B3')
    export_to_drive(image, nom_imgSent, geometry)
def landcover(geometry, destination_path, nombre_cs='Landcover_10m'):
    dataset = ee.ImageCollection('ESA/WorldCover/v200').first()
    image4 = dataset.clip(geometry).unmask()
    export_to_drive(image4, nombre_cs, geometry)
    print(
        f"-Iniciando con las descargas de los archivos en la carpeta {destination_path}-")
    download_from_drive_by_description(nombre_cs, destination_path)
def dem(geometry, destination_path, nombre_dem='ALOSDSM_30m'):
    ALOSDSMDEM = ee.Image('JAXA/ALOS/AW3D30_V1_1')
    ALOSDSM = ALOSDSMDEM.select('AVE').clip(geometry)
    image5 = ALOSDSM.select("AVE")
    export_to_drive(image5, nombre_dem, geometry, scale=30)
    print(
        f"-Iniciando con las descargas de los archivos en la carpeta {destination_path}-")
    download_from_drive_by_description(nombre_dem, destination_path)
def ndwi_med(collection1, geometry, destination_path, nom_imgNDWImedia='NDWI_median'):
    withNDWI = collection1.map(addNDWI)
    medianNDWI = withNDWI.reduce(ee.Reducer.median())
    image2 = medianNDWI.clip(geometry)
    export_to_drive(image2, nom_imgNDWImedia, geometry)
    print(
        f"-Iniciando con las descargas de los archivos en la carpeta {destination_path}-")
    download_from_drive_by_description(nom_imgNDWImedia, destination_path)
def ndwi_max(collection1, geometry, destination_path, nom_imgNDWImax='NDWI_max'):
    withNDWI = collection1.map(addNDWI)
    maxNDWI = withNDWI.reduce(ee.Reducer.max())
    image3 = maxNDWI.clip(geometry)
    export_to_drive(image3, nom_imgNDWImax, geometry)
    print(
        f"-Iniciando con las descargas de los archivos en la carpeta {destination_path}-")
    download_from_drive_by_description(nom_imgNDWImax, destination_path)
