# Agente diário da Vox Dei

Roda todo dia às 5h03 (Brasília). Produz e **agenda** os 3 Shorts do **dia seguinte** (7h, 12h e 20h). Desde 02/11/2026 (decisão da Helo).
A Helo autorizou em 31/10/2026 agendar sem a aprovação dela. Ela é avisada depois e pode pedir mudanças pelo campo `recadoHelo` da agenda ou na conversa.

## Passo a passo

1. `git pull` neste repositório. Leia os `specs/` dos últimos 14 dias para não repetir versículo, gancho, palavra em destaque nem frases.
2. Leia a agenda (`config/semana` e `plano` em https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw) e veja se a Helo deixou `recadoHelo` ou mudou algum tema.
3. Escreva 3 specs em `specs/` (`AAAA-MM-DD-manha.json` 7h, `AAAA-MM-DD-meiodia.json` 12h, `AAAA-MM-DD-noite.json` 20h). **Desde 06/11/2026 (decisão da Helo, opção D) o estilo alterna por DIA**, os 3 horários do dia no mesmo estilo:
   - **Dia "clara"** → `"estilo": "biblia"` (página clara, referência grande, todos os textos entram juntos no fade e depois os grifos coloridos aparecem). `"particulas": false`, `"duracao": 20`.
   - **Dia "foto"** → `"estilo": "biblia-foto"` (foto realista de Bíblia aberta com trecho grifado em AMARELO; imagem parada, sem fade nem animação de grifo; partículas leves + música). Alterne o modelo de Bíblia a cada vídeo (`"modelo"`, ver abaixo).
   - Calendário: 06/11 clara, 07/11 foto, 08/11 clara, 09/11 foto, e assim por diante (dia ímpar de novembro = foto; depois siga alternando, sem repetir o estilo do dia anterior). Confira o `estilo` do último doc em `plano` antes de decidir.
   - Temas: 7h tom de começo de dia (`config/semana.dias`), 12h pausa no meio do dia (`config/semana.meiodia`), 20h oração da noite (paz, sono, entrega, perdão, medo, ansiedade).
   - Os estilos antigos (gigante, marca-texto, manuscrito) foram aposentados depois de 05/11.
   - **Exceção da rodada de 06/11 (sexta):** sábado 07/11 inteiro, o 7h de segunda 09/11 e o 12h e 20h de domingo 08/11 (pão e Guardião, pedido da Helo em 05/11) já estão agendados. Nessa sexta produza só o **7h de domingo 08/11** (clara) e o **12h e 20h de segunda 09/11** (foto, modelos diferentes dos de sábado). Agende no Buffer só o 7h de domingo; segunda 12h/20h ficam com `etapa: "video"` para o sábado agendar.
   - **Exceção da rodada de 05/11:** o 7h de 06/11 (Isaías 41,10) já está pronto e agendado. Produza só o 12h e o 20h de 06/11, no estilo clara.
4. Rode `python3 scripts/make_short.py specs/<spec>.json` para cada um (cerca de 5 min cada). Confira a capa gerada.
5. `git add`, `commit` e `push` em `main`. O link do vídeo para o Buffer é
   `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/<saida>/<nome>.mp4`.
6. No Buffer (canal YouTube "Vox Dei"), **agende** cada post (`mode: customScheduled`, `dueAt` 07:00, 12:00 e 20:00 com `-03:00`), com vídeo, título, descrição e hashtags. Se algo falhar, não agende pela metade: avise a Helo.
7. Suba na agenda, numa única chamada (Artifact publish, `url` da agenda, `asset: true`, `file_paths`), as capas **e os mp4** dos Shorts do dia. Grave `plano/AAAA-MM-DD` (7h), `plano/AAAA-MM-DD-meiodia` (12h) e `plano/AAAA-MM-DD-noite` (20h) num único batch com `etapa: "agendado"`, `estilo`, `capa` ("/_blob/<id>" da capa), `video` ("/_blob/<id>" do mp4, a página mostra o player), `bufferPostId` e os demais campos. A página mostra sozinha as plataformas (YouTube pelo bufferPostId, TikTok pelos campos tiktok/tiktokHora); não republique a página.
8. Mande para a Helo um aviso curto com os títulos e o link da agenda (as capas e vídeos ficam na agenda; a thread já atingiu o limite de anexos, então não anexe arquivos).

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

### Estilo "biblia" (Bíblia grifada clara, adotado em 04/11)

```json
{"nome": "...", "saida": "shorts/2026-11", "estilo": "biblia", "duracao": 20,
 "titulo_leitura": "Isaías 41,10",
 "versiculo_texto": "“==trecho grifado== resto do versículo.”",
 "reflexao": ["Parágrafo com ==grifo== e __palavra sublinhada__.", "...", "Se você crê, escreva ==“Amém”== ..."],
 "cores": ["amarelo", "verde", "rosa", "amarelo"], "particulas": false}
```
- `==texto==` = marca-texto (cor do parágrafo, na ordem de `cores`: amarelo, verde, rosa, azul). `__texto__` = negrito sublinhado.
- Versículo + 2 a 3 parágrafos curtos de reflexão própria (não copie textos de outros canais). Total de até ~90 palavras.
- Exemplo: specs/2026-11-06-manha.json.

### Estilo "biblia-foto" (dias de foto, a partir de 07/11)

```json
{"nome": "...", "saida": "shorts/2026-11", "estilo": "biblia-foto", "duracao": 20, "modelo": 1,
 "titulo_leitura": "Jeremias 29,11", "texto": ["Parágrafo do versículo com ==trecho grifado==.", "..."], "particulas": "leve"}
```
- Texto bíblico fiel (tradução católica), com 1 a 3 trechos `==grifados==` em amarelo. `modelo` escolhe o tipo de página (alterne a cada vídeo).

## Copy (o que mais deu alcance)

- **Título:** o gancho do vídeo, com a palavra em destaque em maiúsculas + emoji + versículo + `#shorts`. Até 100 caracteres. Exemplo: `Você pediu um sinal de DEUS? Reze esta oração 🙏 Salmo 51,12 #shorts`.
- **Descrição:** 1ª linha com urgência ("Não passe sem rezar", "Deus colocou esta oração no seu caminho"), o versículo completo, depois "Escreva AMÉM...", "Deixe o nome de quem..." e "Inscreva-se na Vox Dei...". No fim, de 5 a 6 hashtags (#oração #oraçãocatólica #salmoX #catolicos #shorts).
- YouTube: `categoryId` "22", `madeForKids` false, `isAiGenerated` false (o vídeo não tem cena realista).
