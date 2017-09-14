
from ipyleaflet import Map, ImageOverlay
from folium.features import image_to_url
from owslib.wmts import WebMapTileService
from owslib.wcs import WebCoverageService
import matplotlib.pyplot as plt
from matplotlib.image import imread
import io
import math
import numpy as np

class test:
    
    def __init__(self, lat, lon, zoom=10):
        
        self.lat_center = lat
        self.lon_center = lon
        
        try:
            self.zoom = zoom
        except:
            pass
        
                
        self.map = Map(center=[self.lat_center, self.lon_center],
                       zoom=self.zoom,
                       width='100%',
                       heigth=6000)
    
    def wmtsRequest(self, layer='AGRICULTURE'):
                  
        self.layer = layer  
        
        wmts_url = 'https://services.sentinel-hub.com/v1/wmts/0a968a13-5617-485d-8803-34b0577fd7c7'
        wmts = WebMapTileService(wmts_url)
        
        self.x, self.y = self.deg2num(self.lat_center, self.lon_center, self.zoom)
        
        wmtsOut = wmts.gettile(layer=self.layer,
                            tilematrixset='PopularWebMercator256',
                            tilematrix=self.zoom,
                            row=self.y,
                            column=self.x,
                            format="image/png")
        
        self.imgArr = imread(io.BytesIO(wmtsOut.read()))
        
        self.lat_max, self.lon_min = self.num2deg(self.x, self.y, self.zoom)
        self.lat_min, self.lon_max = self.num2deg(self.x+1, self.y+1, self.zoom)
        
        imgurl = image_to_url(image=self.imgArr)
        self.map.add_layer(ImageOverlay(url=imgurl,
                                        bounds=[[self.lat_min, self.lon_min],
                                                [self.lat_max, self.lon_max]]))
        
    def wcsRequest(self, layer='AGRICULTURE'):
        
        from PIL import Image
        
        self.layer = layer
        wcs_url = 'https://services.sentinel-hub.com/v1/wcs/0a968a13-5617-485d-8803-34b0577fd7c7'
        wcs = WebCoverageService(wcs_url, version='1.0.0')
        
        self.x, self.y = self.deg2num(self.lat_center, self.lon_center, self.zoom)
        self.lat_max, self.lon_min = self.num2deg(self.x, self.y, self.zoom)
        self.lat_min, self.lon_max = self.num2deg(self.x+1, self.y+1, self.zoom)
        
        from pyproj import Proj, transform

        inProj = Proj(init='epsg:4326')
        outProj = Proj(init='epsg:3857')
        x1,y1 = transform(inProj,outProj,self.lon_min,self.lat_min)
        x2,y2 = transform(inProj,outProj,self.lon_max,self.lat_max)
        
        bb=(x1, y1, x2, y2)
        
        wcsOut = wcs.getCoverage(identifier=self.layer,
                                 time=None,
                                 width=1000,
                                 height=1000,
                                 bbox = bb,
                                 format = 'GeoTIFF')
        
        self.imgTiff = Image.open(wcsOut)
        self.imgArr = np.array(self.imgTiff)
        
        imgurl = image_to_url(image=self.imgArr)
        self.map.add_layer(ImageOverlay(url=imgurl,
                                        bounds=[[self.lat_min, self.lon_min],
                                                [self.lat_max, self.lon_max]]))
        
    def mapUpdate(self):
        
        self.lat_center, self.lon_center = self.map.center
        
        self.wcsRequest()
    
    def deg2num(self, lat, lon, zoom):
        
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        xtile = int((lon + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def num2deg(self, xtile, ytile, zoom):
        """returns NW corners, for other corners, use xtile+1 and/or
        ytile+1"""
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)
