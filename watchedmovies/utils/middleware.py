from compression_middleware.middleware import CompressionMiddleware


class SkipImagesCompressionMiddleware(CompressionMiddleware):
    """
    Comprime las respuestas con Brotli/zstd/gzip, salvo las imágenes.

    Los JPEG y PNG (posters y wrapped) ya vienen comprimidos: intentar de nuevo
    gasta CPU del worker y el resultado se descarta por no mejorar el tamaño.
    """

    def process_response(self, request, response):
        if response.get("Content-Type", "").startswith("image/"):
            return response
        return super().process_response(request, response)
