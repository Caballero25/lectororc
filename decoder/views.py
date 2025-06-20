import easyocr
import base64
from io import BytesIO
import numpy as np
from PIL import Image
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
import re

class OcrTextExtractView(APIView):
    """
    API para recibir imágenes y extraer texto usando EasyOCR.
    """
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def preprocess_image(self, img):
        """
        Preprocesa la imagen para mejorar la precisión del OCR.
        Convierte a escala de grises y mejora el contraste.
        """
        # Reducir tamaño de la imagen para mejorar velocidad
        max_size = (1000, 1000)  # Limitar a 1000x1000 píxeles
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Convertir a escala de grises
        gray_img = img.convert("L")
        return gray_img

    def post(self, request):
        # 1) Obtener la imagen (Base64 o multipart)
        image_b64 = request.data.get("image")
        uploaded_file = request.FILES.get("image")

        if not image_b64 and not uploaded_file:
            return Response(
                {"detail": "Falta imagen"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if image_b64:
                if "," in image_b64:
                    image_b64 = image_b64.split(",", 1)[1]
                image_bytes = base64.b64decode(image_b64)
            else:
                image_bytes = uploaded_file.read()

            img = Image.open(BytesIO(image_bytes))
        except Exception:
            return Response(
                {"detail": "Imagen inválida"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2) Preprocesar la imagen
        processed_img = self.preprocess_image(img)

        # Convertir la imagen PIL a un array de Numpy
        processed_img_np = np.array(processed_img)

        # 3) Crear el lector OCR
        reader = easyocr.Reader(['en'], gpu=False)  # Usar el idioma inglés, puedes añadir más idiomas si es necesario

        # 4) Extraer el texto con OCR
        result = reader.readtext(processed_img_np)  # Usar el array de Numpy

        # 5) Extraer solo el texto, limpiar el resultado
        extracted_text = " ".join([text[1] for text in result])
        
        # 6) Limpiar el texto: convertir a mayúsculas, eliminar caracteres especiales y espacios
        clean_text = re.sub(r"[^A-Za-z0-9]", "", extracted_text).upper()
        print(clean_text)

        return Response({"text": clean_text}, status=status.HTTP_200_OK)
