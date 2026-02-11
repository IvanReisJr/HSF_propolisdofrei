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


class DistributorSimulatorMiddleware:
    """
    Middleware para simular a visão de um distribuidor específico para superusuários.
    Intercepta request.user e modifica request.user.distributor se uma simulação estiver ativa na sessão.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            # Import aqui para evitar problemas de carregamento circular
            from apps.distributors.models import Distributor
            
            simulated_id = request.session.get('simulated_distributor_id')
            if simulated_id:
                try:
                    distributor = Distributor.objects.get(id=simulated_id)
                    # Monkey-patch no objeto user da request
                    request.user.distributor = distributor
                    request.is_simulating = True
                except Distributor.DoesNotExist:
                    # Se não existir (ex: foi deletado), remove da sessão
                    if 'simulated_distributor_id' in request.session:
                        del request.session['simulated_distributor_id']
                    request.is_simulating = False
            else:
                request.is_simulating = False
        else:
            request.is_simulating = False
        
        response = self.get_response(request)
        return response
