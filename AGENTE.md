# Agente diário da Vox Dei

Roda todo dia às 5h03 (Brasília). Produz e **agenda** os 3 Shorts do **dia seguinte** (7h, 12h e 20h). Desde 02/11/2026 (decisão da Helo).
A Helo autorizou em 31/10/2026 agendar sem a aprovação dela. Ela é avisada depois e pode pedir mudanças pelo campo `recadoHelo` da agenda ou na conversa.

## Passo a passo

1. `git pull` neste repositório. Leia os `specs/` dos últimos 14 dias para não repetir versículo, gancho, palavra em destaque nem frases.
2. Leia a agenda (`config/semana` e `plano` em https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw) e veja se a Helo deixou `recadoHelo` ou mudou algum tema.
3. Escreva 3 specs em `specs/`, cada um com o seu estilo fixo (Helo, 02/11/2026; estudo de design https://claude.ai/artifact/DhcC7adX4RarDuZq7SRhED):
   - `AAAA-MM-DD-manha.json`, 7h, `"estilo": "gigante"` (variação 8: preto, letras condensadas enormes, destaque amarelo), `"particulas": false`. Tema do dia em `config/semana.dias` (dom Salmo 23, seg família, ter cura, qua Nossa Senhora, qui ansiedade, sex perdão, sáb proteção). Tom de começo de dia.
   - `AAAA-MM-DD-meiodia.json`, 12h, `"estilo": "marca-texto"` (variação 4: branco, letras grossas, destaque com marca-texto amarelo), `"particulas": false`. Tema em `config/semana.meiodia` (dom gratidão pela semana, seg força no trabalho, ter gratidão, qua Ângelus, qui pão de cada dia, sex Sagrado Coração, sáb Anjo da Guarda). Tom de pausa no meio do dia.
   - `AAAA-MM-DD-noite.json`, 20h, `"estilo": "manuscrito"` (variação 3: pergaminho, moldura dourada, letra capitular), `"particulas": "leve"`. Oração da noite (paz, sono, entrega, perdão, medo, ansiedade). Tom de fim de dia.
   - O teste A/B de partículas acabou (Helo gostou): só a noite leva partículas, sempre leves.
   - No estilo manuscrito a oração é reescrita automaticamente em parágrafo; comece o 1º parágrafo com uma letra (não aspas) para sair a capitular.
4. Rode `python3 scripts/make_short.py specs/<spec>.json` para cada um (cerca de 5 min cada). Confira a capa gerada.
5. `git add`, `commit` e `push` em `main`. O link do vídeo para o Buffer é
   `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/<saida>/<nome>.mp4`.
6. No Buffer (canal YouTube "Vox Dei"), **agende** cada post (`mode: customScheduled`, `dueAt` 07:00, 12:00 e 20:00 com `-03:00`), com vídeo, título, descrição e hashtags. Se algo falhar, não agende pela metade: avise a Helo.
7. Suba na agenda, numa única chamada (Artifact publish, `url` da agenda, `asset: true`, `file_paths`), as capas **e os mp4** dos Shorts do dia. Grave `plano/AAAA-MM-DD` (7h), `plano/AAAA-MM-DD-meiodia` (12h) e `plano/AAAA-MM-DD-noite` (20h) num único batch com `etapa: "agendado"`, `estilo`, `capa` ("/_blob/<id>" da capa), `video` ("/_blob/<id>" do mp4, a página mostra o player), `bufferPostId` e os demais campos. A página mostra sozinha as plataformas (YouTube pelo bufferPostId, TikTok pelos campos tiktok/tiktokHora); não republique a página.
8. Mande para a Helo um aviso curto com as capas e os títulos do que foi agendado.

## Regra de sexta-feira (pedido da Helo, 03/11/2026)

A Helo agenda os TikToks do fim de semana na sexta às 19h50. Por isso:
- **Sexta (rodada das 5h03):** produza os Shorts de **sábado, domingo e segunda** (3 horários cada, 9 vídeos), todos com commit e push no `main`. No Buffer, agende só **sábado e domingo** (com os 3 de sexta ainda na fila dá 9, dentro do limite de 10). Grave os docs de segunda na agenda com `etapa: "video"` e a nota "produzido na sexta; agendar no Buffer no sábado".
- **Sábado:** não produza nada novo. Só agende no Buffer os 3 de segunda (já estão no repositório) e atualize os docs de segunda para `etapa: "agendado"` com `bufferPostId`.
- **Domingo:** volta ao normal (produz terça).
- Antes de agendar, conte os posts agendados no Buffer; nunca passe de 10.

## Formato do spec

```json
{
  "nome": "2026-11-02-manha-familia",
  "saida": "shorts/2026-11",
  "gancho_antes": "Você pediu um sinal de",
  "destaque": "DEUS",
  "gancho_depois": "Aqui está.",
  "oracao": [["linha 1", "linha 2"], ["linha 3", "linha 4"]],
  "referencia": "Salmo 127,1",
  "cta": "Escreva AMÉM se você recebe esta oração",
  "estilo": "gigante",
  "particulas": false
}
```

- `destaque`: uma palavra curta em maiúsculas (DEUS, JESUS, MARIA, AMÉM, PAZ...). Varie entre os dias.
- No máximo 11 linhas de oração, até cerca de 32 caracteres por linha. O script reduz a fonte para caber e para com erro se o texto não couber acima da área do título.
- Plano grátis do Buffer segura 10 agendados: com 3 por dia, não agende mais que o dia seguinte.
- Público católico: pode usar Ave-Maria, Nossa Senhora, santos e o Anjo da Guarda. Cite os versículos corretamente (numeração da Bíblia católica, com vírgula: Salmo 4,9).

## Copy (o que mais deu alcance)

- **Título:** o gancho do vídeo, com a palavra em destaque em maiúsculas + emoji + versículo + `#shorts`. Até 100 caracteres. Exemplo: `Você pediu um sinal de DEUS? Reze esta oração 🙏 Salmo 51,12 #shorts`.
- **Descrição:** 1ª linha com urgência ("Não passe sem rezar", "Deus colocou esta oração no seu caminho"), o versículo completo, depois "Escreva AMÉM...", "Deixe o nome de quem..." e "Inscreva-se na Vox Dei...". No fim, de 5 a 6 hashtags (#oração #oraçãocatólica #salmoX #catolicos #shorts).
- YouTube: `categoryId` "22", `madeForKids` false, `isAiGenerated` false (o vídeo não tem cena realista).
