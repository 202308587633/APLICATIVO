from urllib.parse import urlencode

class BDTDAdapter:
    BASE_URL = "https://bdtd.ibict.br/vufind/Search/Results"

    def __init__(self, termo_principal):
        self.query_params = []
        self.query_params.append(('join', 'AND'))
        # Adiciona o termo do usuário em "Todos os Campos" (AllFields)
        self._add_param(termo_principal, 'AND', 'AllFields')

    def _add_param(self, term, operator, field_type='AllFields'):
        self.query_params.append(('bool0[]', operator))
        self.query_params.append(('lookfor0[]', term))
        self.query_params.append(('type0[]', field_type))

    def add_inclusion(self, term):
        self._add_param(term, 'AND', 'AllFields')
        return self

    def add_subject_restriction(self, subject):
        """Adiciona restrição de Assunto (Subject)"""
        self._add_param(subject, 'AND', 'Subject')
        return self

    def get_url(self, page=1, year=None):
        final_params = self.query_params.copy()
        final_params.append(('page', str(page)))
        
        if year:
            # Parâmetros exatos de data da BDTD
            final_params.append(('daterange[]', 'publishDate'))
            final_params.append(('publishDatefrom', str(year)))
            final_params.append(('publishDateto', str(year)))
        
        return f"{self.BASE_URL}?{urlencode(final_params)}"