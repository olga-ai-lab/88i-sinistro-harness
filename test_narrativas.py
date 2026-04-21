"""
Suite de testes manual — rode com: python test_narrativas.py

3 casos cuidadosamente desenhados para validar cada rota:
  1. Caminho feliz → pronto_para_analise
  2. Narrativa ambígua → solicitar_esclarecimento
  3. Narrativa suspeita → escalar_humano

Em produção, estes casos viram um dataset no Langfuse para eval contínua.
"""

from agent import processar_narrativa

CASOS = [
    {
        "nome": "1. CAMINHO FELIZ - Motorista app com acidente documentado",
        "esperado": "pronto_para_analise",
        "narrativa": """
        Oi boa tarde, meu nome é João Silva, sou motorista de app da Uber Eats.
        Ontem à noite, dia 18 de abril, por volta das 22h, bati minha moto Honda
        CG 160 placa ABC1D23 na Av Paulista altura do 1500 em São Paulo.
        Um carro virou na minha frente sem dar seta. Tô com a perna direita
        quebrada, fui no Hospital das Clínicas e o médico me deu atestado de 30
        dias parado. Já fiz o BO na delegacia online, tenho o número do protocolo.
        Preciso abrir o sinistro pra receber a diária de impedimento.
        """,
    },
    {
        "nome": "2. AMBÍGUO - Narrativa pobre",
        "esperado": "solicitar_esclarecimento",
        "narrativa": "sumiu minha encomenda",
    },
    {
        "nome": "3. SUSPEITO - Múltiplas red flags",
        "esperado": "escalar_humano",
        "narrativa": """
        Tive um acidente semana passada, acho que foi terça ou quarta não lembro
        direito. Caí da moto sozinho numa rua que não lembro o nome. Não tem BO
        nem foto porque ninguém viu. Quebrei o braço. O médico disse 90 dias parado.
        Preciso do valor máximo do seguro urgente porque estou sem trabalhar.
        """,
    },
]


def executar():
    for i, caso in enumerate(CASOS, 1):
        print("\n" + "█" * 70)
        print(f"CASO {caso['nome']}")
        print(f"Rota esperada: {caso['esperado']}")
        print("█" * 70)

        resultado = processar_narrativa(caso["narrativa"].strip())

        rota_real = resultado["proxima_acao"]
        status = "✅ PASS" if rota_real == caso["esperado"] else "❌ FAIL"
        print(f"\n{status} — rota real: {rota_real}")

        if resultado.get("extracao"):
            ex = resultado["extracao"]
            print(f"  • tipo_sinistro: {ex.tipo_sinistro}")
            print(f"  • urgência: {ex.urgencia}")
            print(f"  • confiança: {ex.confianca:.2f}")
            print(f"  • feridos: {ex.ha_feridos} | fatais: {ex.ha_vitimas_fatais}")
            print(f"  • campos_faltantes: {len(ex.campos_faltantes)}")
            print(f"  • red_flags: {len(ex.red_flags)}")
            if ex.red_flags:
                for rf in ex.red_flags:
                    print(f"      ⚠ [{rf.severidade}] {rf.descricao}")

        print(f"\n  Mensagem ao segurado:")
        for linha in (resultado.get("mensagem_ao_segurado") or "").split("\n"):
            print(f"    {linha}")


if __name__ == "__main__":
    executar()
