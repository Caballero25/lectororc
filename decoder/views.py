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

try:
    print("Initializing EasyOCR Reader...")
    # Asegúrate de usar los idiomas que necesitas.
    READER = easyocr.Reader(['en'], gpu=False) 
    print("EasyOCR Reader initialized successfully.")
except Exception as e:
    # Manejar el caso en que el lector no pueda inicializarse
    print(f"Error initializing EasyOCR Reader: {e}")
    READER = None


class OcrTextExtractView(APIView):
    """
    API para recibir imágenes y extraer texto usando una instancia global de EasyOCR.
    """
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def preprocess_image(self, img):
        """
        Preprocesa la imagen para mejorar la precisión del OCR.
        """
        max_size = (1000, 1000)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        gray_img = img.convert("L")
        return gray_img

    def post(self, request):
        # Verificar si el lector se inicializó correctamente al arrancar
        if READER is None:
            return Response(
                {"detail": "OCR service is not available"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        # 1) Obtener la imagen
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
        processed_img_np = np.array(processed_img)

        # 3) Extraer el texto con OCR usando la instancia GLOBAL
        # Ya no se crea un nuevo lector, solo se usa el que ya existe.
        result = READER.readtext(processed_img_np)

        # 4) Extraer y limpiar el texto
        extracted_text = " ".join([text[1] for text in result])
        clean_text = re.sub(r"[^A-Za-z0-9]", "", extracted_text).upper()
        print(clean_text)

        return Response({"text": clean_text}, status=status.HTTP_200_OK)