class HtmxMiddleware:
    """
    Middleware para detectar se a requisição é do HTMX e adicionar 
    o atributo 'htmx' ao objeto request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Adiciona flag booleana se o cabeçalho HX-Request estiver presente
        request.htmx = request.headers.get('HX-Request') == 'true'
        
        response = self.get_response(request)
        return response
