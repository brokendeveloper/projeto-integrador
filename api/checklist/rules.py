REQUISITOS_HABILITACAO = [
    {
        "id": "jur_01",
        "categoria": "Habilitação Jurídica",
        "descricao": "Certificado de Condição de Microempreendedor Individual (CCMEI)",
        "base_legal": "Art. 66, II, Lei 14.133/2021",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "jur_02",
        "categoria": "Habilitação Jurídica",
        "descricao": "Comprovante de inscrição no CNPJ",
        "base_legal": "Art. 66, I, Lei 14.133/2021",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "fis_01",
        "categoria": "Regularidade Fiscal e Trabalhista",
        "descricao": "Certidão Negativa de Débitos Federais (CND/CPEN)",
        "base_legal": "Art. 68, I, Lei 14.133/2021",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "fis_02",
        "categoria": "Regularidade Fiscal e Trabalhista",
        "descricao": "Certidão de Regularidade do FGTS (CRF)",
        "base_legal": "Art. 68, IV, Lei 14.133/2021",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "fis_03",
        "categoria": "Regularidade Fiscal e Trabalhista",
        "descricao": "Certidão Negativa de Débitos Trabalhistas (CNDT)",
        "base_legal": "Art. 68, V, Lei 14.133/2021",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "eco_01",
        "categoria": "Qualificação Econômico-Financeira",
        "descricao": "Declaração de que não está sujeito à falência (MEI dispensado de balanço)",
        "base_legal": "Art. 69 c/c Art. 4-A, LC 123/2006",
        "obrigatorio": True,
        "plano": "free",
    },
    {
        "id": "mei_01",
        "categoria": "Benefícios MEI",
        "descricao": "Declaração de enquadramento como MEI para preferência em licitações até R$ 80.000,00",
        "base_legal": "Art. 4-A, LC 123/2006 c/c Art. 49, Lei 14.133/2021",
        "obrigatorio": False,
        "plano": "free",
    },
    {
        "id": "mei_02",
        "categoria": "Benefícios MEI",
        "descricao": "Declaração de que não há impedimento de participação em licitação exclusiva para MEI",
        "base_legal": "Art. 48, I, LC 123/2006",
        "obrigatorio": False,
        "plano": "premium",
    },
]


def montar_checklist(plano_usuario: str = "free") -> list[dict]:
    return [r for r in REQUISITOS_HABILITACAO if r["plano"] == "free" or plano_usuario == "premium"]
