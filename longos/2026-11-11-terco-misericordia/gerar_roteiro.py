"""Gera roteiro-tts.json (uma fala por tela) do Terço da Misericórdia de 11/11/2026."""
import json, os
T = "TERÇO DA MISERICÓRDIA"
S = []
def add(fala, tela=None, titulo=T, contador="", pausa=1.2, mostrar=True):
    S.append({"fala": fala, "tela": (tela if tela is not None else fala) if mostrar else "",
              "titulo": titulo, "contador": contador, "pausa": pausa})

add("São três horas da tarde, a Hora da Misericórdia. Hoje vamos rezar juntos o Terço da Misericórdia pelas famílias que estão passando por dificuldades: pela saúde, pelo sustento e pela paz dentro de casa.",
    tela="Hoje rezamos pelas famílias que passam por dificuldades:\n\npela saúde, pelo sustento e pela paz dentro de casa.", titulo="QUARTA-FEIRA · INTENÇÃO DO DIA", pausa=1.5)
add("Antes de começar, deixe aqui nos comentários a sua intenção. Escreva o nome da pessoa ou da situação que você quer entregar a Jesus hoje. Vamos rezar por cada uma delas.",
    tela="Deixe sua intenção nos comentários\n\nEscreva o nome da pessoa ou da situação que você quer entregar a Jesus hoje.", titulo="ANTES DE COMEÇAR", pausa=1.5)
add("Coloque-se na presença de Deus. Respire fundo. Jesus está aqui.", tela="Coloque-se na presença de Deus.\n\nRespire fundo.\nJesus está aqui.", titulo="", pausa=3.0)

add("Em nome do Pai, e do Filho, e do Espírito Santo. Amém.", titulo="SINAL DA CRUZ", pausa=1.5)
add("Expirastes, Jesus, mas a fonte da vida jorrou para as almas, e abriu-se o oceano de misericórdia para o mundo inteiro. Ó fonte de vida, insondável misericórdia divina, envolvei o mundo inteiro e derramai-vos sobre nós.",
    titulo="ORAÇÃO INICIAL", pausa=1.5)
for i in range(3):
    add("Ó Sangue e Água, que jorrastes do Coração de Jesus como fonte de misericórdia para nós, eu confio em vós.",
        titulo="ORAÇÃO INICIAL", contador=f"{i+1}/3", pausa=1.0)
add("Pai Nosso, que estais no céu, santificado seja o vosso nome, venha a nós o vosso reino, seja feita a vossa vontade, assim na terra como no céu. O pão nosso de cada dia nos dai hoje, perdoai-nos as nossas ofensas, assim como nós perdoamos a quem nos tem ofendido, e não nos deixeis cair em tentação, mas livrai-nos do mal. Amém.",
    titulo="PAI NOSSO", pausa=1.5)
add("Ave Maria, cheia de graça, o Senhor é convosco, bendita sois vós entre as mulheres e bendito é o fruto do vosso ventre, Jesus. Santa Maria, Mãe de Deus, rogai por nós pecadores, agora e na hora da nossa morte. Amém.",
    titulo="AVE MARIA", pausa=1.5)
add("Creio em Deus Pai todo-poderoso, criador do céu e da terra; e em Jesus Cristo, seu único Filho, nosso Senhor, que foi concebido pelo poder do Espírito Santo, nasceu da Virgem Maria, padeceu sob Pôncio Pilatos, foi crucificado, morto e sepultado.",
    titulo="CREIO", pausa=0.6)
add("Desceu à mansão dos mortos, ressuscitou ao terceiro dia, subiu aos céus, está sentado à direita de Deus Pai todo-poderoso, donde há de vir a julgar os vivos e os mortos. Creio no Espírito Santo, na santa Igreja Católica, na comunhão dos santos, na remissão dos pecados, na ressurreição da carne, na vida eterna. Amém.",
    titulo="CREIO", pausa=2.0)

intencoes = [
    "Pelas famílias que estão doentes, para que Jesus traga cura e força.",
    "Pelas famílias que passam por aperto financeiro, para que nunca falte o pão na mesa.",
    "Pelos lares onde há brigas e mágoas, para que voltem o perdão e a paz.",
    "Pelos filhos que se afastaram de casa e de Deus, para que encontrem o caminho de volta.",
    "Por todas as intenções deixadas nos comentários, e pela sua família, que está rezando agora.",
]
ord_ = ["PRIMEIRA", "SEGUNDA", "TERCEIRA", "QUARTA", "QUINTA"]
for d in range(5):
    tit = f"{ord_[d]} DEZENA"
    add(f"{ord_[d].capitalize()} dezena. {intencoes[d]}", tela=intencoes[d], titulo=tit, pausa=1.5)
    add("Eterno Pai, eu vos ofereço o Corpo e Sangue, Alma e Divindade de vosso diletíssimo Filho, Nosso Senhor Jesus Cristo, em expiação dos nossos pecados e dos do mundo inteiro.",
        titulo=tit, pausa=1.2)
    for k in range(10):
        add("Pela sua dolorosa paixão, tende misericórdia de nós e do mundo inteiro.",
            titulo=tit, contador=f"{k+1}/10", pausa=0.9 if k < 9 else 2.0)

for i in range(3):
    add("Deus Santo, Deus Forte, Deus Imortal, tende piedade de nós e do mundo inteiro.",
        titulo="ORAÇÃO FINAL", contador=f"{i+1}/3", pausa=1.0)
add("Ó Sangue e Água, que jorrastes do Coração de Jesus como fonte de misericórdia para nós, eu confio em vós.", titulo="ORAÇÃO FINAL", pausa=1.5)
for i in range(3):
    add("Jesus, eu confio em vós.", titulo="ORAÇÃO FINAL", contador=f"{i+1}/3", pausa=1.2)
add("Em nome do Pai, e do Filho, e do Espírito Santo. Amém.", titulo="SINAL DA CRUZ", pausa=2.0)
add("Obrigada por rezar comigo hoje. Se este terço tocou o seu coração, escreva Amém nos comentários e compartilhe com alguém da sua família que precisa dessa oração. Toda quarta-feira, às três da tarde, a gente se encontra aqui de novo para rezar o Terço da Misericórdia. Fique com Deus.",
    tela="Escreva AMÉM nos comentários\n\nToda quarta-feira, às 15h,\nrezamos juntos o Terço da Misericórdia.", titulo="FIQUE COM DEUS", pausa=4.0)

# Áudios únicos: falas repetidas reaproveitam o mesmo arquivo (a voz demora ~20 min por minuto).
# A jaculatória do terço tem 2 versões alternadas para não soar repetida.
uniq = {}
for i, s in enumerate(S, 1):
    s["id"] = f"{i:03d}"
    key = s["fala"]
    if key.startswith("Pela sua dolorosa"):
        key = key + ("#B" if s["contador"] and int(s["contador"].split("/")[0]) % 2 == 0 else "#A")
    if key not in uniq:
        uniq[key] = f"{len(uniq)+1:02d}"
    s["audio"] = uniq[key]
here = os.path.dirname(os.path.abspath(__file__))
json.dump({"titulo": "Terço da Misericórdia — 11/11/2026", "fundo": "imagens/fundo-jesus-vela.png",
           "vela": [0.929, 0.744], "segmentos": S}, open(os.path.join(here, "roteiro-tts.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
with open(os.path.join(here, "roteiro-voz.txt"), "w", encoding="utf-8") as f:
    f.write("ROTEIRO PARA A VOZ — Terço da Misericórdia (quarta 11/11)\n"
            "Gere um arquivo de áudio para cada bloco e salve com o número do bloco (01.wav, 02.wav ...).\n"
            "As falas repetidas do terço são reaproveitadas na montagem, então são só %d áudios.\n\n" % len(uniq))
    for key, n in uniq.items():
        f.write(f"[{n}]\n{key.split('#')[0]}\n\n")
print(len(S), "segmentos;", len(uniq), "audios;", sum(len(k.split('#')[0].split()) for k in uniq), "palavras a gravar")
