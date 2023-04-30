from fastapi import FastAPI, Response
from picamera import PiCamera
from io import BytesIO
from time import sleep
from typing import Union

app = FastAPI()

@app.get("/capture")
def capture(
    width: Union[int, None] = None, 
    height: Union[int, None] = None, 
    format: Union[str, None] = 'png',
    brightness: Union[int, None] = None,
    contrast: Union[int, None] = None,
    night: Union[bool, None] = None
    ):
    photo_stream = BytesIO()
    
    camera = PiCamera()

    if width is not None and height is not None:
        camera.resolution = (width, height)

    if brightness is not None:
        camera.brightness = brightness

    if contrast is not None:
        camera.contrast = contrast

    if night is not None:
        camera.exposure_mode = 'night'
    

    camera.start_preview()
    sleep(2)
    camera.capture(photo_stream, format)
    camera.stop_preview()
    camera.close()

    photo_stream.seek(0)
    photo = photo_stream.read()
    photo_stream.close()
    return Response(content=photo, media_type=f'image/{format}')
