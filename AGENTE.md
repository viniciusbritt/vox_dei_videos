# Agente diário da Vox Dei

Roda todo dia às 5h03 (Brasília). Produz e **agenda** os 2 Shorts do **dia seguinte** (7h e 20h).
A Helo autorizou em 31/10/2026 agendar sem a aprovação dela. Ela é avisada depois e pode pedir mudanças pelo campo `recadoHelo` da agenda ou na conversa.

## Passo a passo

1. `git pull` neste repositório. Leia os `specs/` dos últimos 14 dias para não repetir versículo, gancho, palavra em destaque nem frases.
2. Leia a agenda (`config/semana` e `plano` em https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw) e veja se a Helo deixou `recadoHelo` ou mudou algum tema.
3. Escreva 2 specs em `specs/`:
   - `AAAA-MM-DD-manha.json`: tema do dia em `config/semana` (dom Salmo 23, seg família, ter cura, qua Nossa Senhora, qui ansiedade, sex perdão, sáb proteção). Tom de começo de dia.
   - `AAAA-MM-DD-noite.json`: oração da noite (paz, sono, entrega, perdão, medo, ansiedade). Tom de fim de dia.
   - **Teste A/B de partículas (pedido da Helo, 31/10):** em cada dia, só UM dos dois Shorts leva `"particulas": true` (partículas douradas subindo). Dia do mês par: o da manhã leva; dia ímpar: o da noite leva. Assim os dois horários testam com e sem. Grave `"particulas": true/false` no doc da agenda.
4. Rode `python3 scripts/make_short.py specs/<spec>.json` para cada um (cerca de 5 min cada). Confira a capa gerada.
5. `git add`, `commit` e `push` em `main`. O link do vídeo para o Buffer é
   `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/<saida>/<nome>.mp4`.
6. No Buffer (canal YouTube "Vox Dei"), **agende** cada post (`mode: customScheduled`, `dueAt` 07:00 e 20:00 com `-03:00`), com vídeo, título, descrição e hashtags. Se algo falhar, não agende pela metade: avise a Helo.
7. Suba a capa na agenda (Artifact publish, `asset: true`) e grave `plano/AAAA-MM-DD` (7h) e `plano/AAAA-MM-DD-noite` (20h) com `etapa: "agendado"`, `capa`, `bufferPostId` e os demais campos.
8. Mande para a Helo um aviso curto com as capas e os títulos do que foi agendado.

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
  "particulas": true
}
```

- `destaque`: uma palavra curta em maiúsculas (DEUS, JESUS, MARIA, AMÉM, PAZ...). Varie entre os dias.
- No máximo 11 linhas de oração, até cerca de 32 caracteres por linha. O script para com erro se uma linha ficar larga demais.
- Público católico: pode usar Ave-Maria, Nossa Senhora, santos e o Anjo da Guarda. Cite os versículos corretamente (numeração da Bíblia católica, com vírgula: Salmo 4,9).

## Copy (o que mais deu alcance)

- **Título:** o gancho do vídeo, com a palavra em destaque em maiúsculas + emoji + versículo + `#shorts`. Até 100 caracteres. Exemplo: `Você pediu um sinal de DEUS? Reze esta oração 🙏 Salmo 51,12 #shorts`.
- **Descrição:** 1ª linha com urgência ("Não passe sem rezar", "Deus colocou esta oração no seu caminho"), o versículo completo, depois "Escreva AMÉM...", "Deixe o nome de quem..." e "Inscreva-se na Vox Dei...". No fim, de 5 a 6 hashtags (#oração #oraçãocatólica #salmoX #catolicos #shorts).
- YouTube: `categoryId` "22", `madeForKids` false, `isAiGenerated` false (o vídeo não tem cena realista).
