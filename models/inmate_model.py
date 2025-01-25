# models/inmate_model.py

class Inmate:
    """
    Classe que representa os dados de um detento (interno).
    Adicione ou remova campos conforme a necessidade do seu projeto.
    """

    def __init__(
        self,
        code: str,
        name: str = 'NÃO INFORMADO',
        mother_name: str = 'NÃO INFORMADO',
        father_name: str = 'NÃO INFORMADO',
        sex: str = 'NÃO INFORMADO',
        birth_date: str = 'NÃO INFORMADO',
        city_origin: str = 'NÃO INFORMADO',
        state: str = 'NÃO INFORMADO',
        country: str = 'NÃO INFORMADO',
        marital_status: str = 'NÃO INFORMADO',
        children_count: str = 'NÃO INFORMADO',
        education: str = 'NÃO INFORMADO',
        religion: str = 'NÃO INFORMADO',
        profession: str = 'NÃO INFORMADO',
        color: str = 'NÃO INFORMADO',
        height: str = 'NÃO INFORMADO',
        modus_operandi: str = 'NÃO INFORMADO',
        sentence_days: str = 'NÃO INFORMADO'
    ):
        # Campos básicos
        self.code = code
        self.name = name  # Nome do interno

        # Novos campos
        self.mother_name = mother_name
        self.father_name = father_name
        self.sex = sex
        self.birth_date = birth_date
        self.city_origin = city_origin
        self.state = state
        self.country = country
        self.marital_status = marital_status
        self.children_count = children_count
        self.education = education
        self.religion = religion
        self.profession = profession
        self.color = color
        self.height = height
        self.modus_operandi = modus_operandi
        self.sentence_days = sentence_days
