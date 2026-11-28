# Agente diário do canal "Salmos do Céu" (antes Vox Dei)

> NOME NOVO (19/11, Helo): **Salmos do Céu**. Nos vídeos, títulos, descrições e marca d'água NÃO usar "Vox Dei" nem "Oração Católica"; usar "orar/oração" em vez de "rezar/reze". Detalhes em /mnt/project-files/mentor/NOME-DO-CANAL.md. Os nomes antigos abaixo (repo, Buffer, "Inscreva-se na Vox Dei") são só históricos: troque por "Salmos do Céu".


Roda às 5h03 (Brasília) e cuida dos Shorts do **dia seguinte**. Leia só este arquivo; não precisa reler histórico de thread.
Autorização: a Helo liberou agendar Shorts sem aprovação dela (31/10/2026). Exceção atual: ver "Frequência".

## Frequência (a única parte que muda)

| Modo | Shorts por dia | Horários |
|---|---|---|
| **Recuperação (ATUAL, desde 12/11)** | 1 | 7h, alternando Bíblia (dia par) e corte do longo (dia ímpar) |
| Recuperado (3 dias seguidos >300 views em 24h, aviso do Tráfego) | 3 | 7h Bíblia, 12h corte, 20h corte |
| Estável por 2 semanas | 4 | teste, a definir com a Helo |

- Para mudar de modo, troque só a linha marcada **ATUAL**.
- Cortes do longo chegam prontos da thread de cortes em `/mnt/project-files/cortes/AAAA-MM-DD/` (mp4 + jpg + título/descrição). O agente só agenda.
- Buffer grátis = no máximo 10 agendados. Conte antes de agendar.
- Rodada de sexta: se precisar adiantar o fim de semana, produza sábado a segunda e agende o que couber nos 10.

## Passo a passo

0. Leia `/mnt/project-files/mentor/MODELO-DA-VEZ.md` (campeão, núcleo, testes e o que parar; atualizado pelo Mentor de canais dark). Não repita o gancho "PARE e reze comigo".

1. `git pull` em `main`. Liste os `specs/` dos últimos 14 dias (só `referencia`/`titulo_leitura`) para não repetir versículo.
2. Leia na agenda (https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw, ArtifactData) só os docs `plano/<amanhã>*` e `recadoHelo`, se houver.
3. Escreva o spec em `specs/AAAA-MM-DD-manha.json` (12h = `-meiodia`, 20h = `-noite`) e rode `python3 scripts/make_short.py specs/<spec>.json`. Confira a capa.
4. `git add`, `commit` e `push` em `main`. Link para o Buffer: `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/<saida>/<nome>.mp4`.
5. Buffer (org `6ae2bc4082663d76d494c180`, canal YouTube Vox Dei `6ae66aff2f1f5ed648384566`): `create_post`, `mode: customScheduled`, `dueAt` com `-03:00`. Se algo falhar, não agende pela metade e avise a Helo.
6. Agenda: suba **só a capa** (Artifact publish, `url` da agenda, `asset: true`) e grave `plano/<dia>` num único batch com `etapa: "agendado"`, `capa: "/_blob/<id>"`, `bufferPostId`, `titulo`, `versiculo`, `estilo`, `arquivo` (link raw do mp4). Não suba o mp4.
7. Aviso à Helo: 1 linha com o título e o horário. Se só conferiu e está tudo certo, não mande nada.

## Estilo atual dos Shorts (Bíblia)

- `"estilo": "biblia-foto"`, `"duracao": 20`, `"particulas": "leve"`, `"modelo"` 1 a 4 alternando a cada vídeo (papel, fonte e enquadramento variados: o canal caiu por repetição em massa).
- Texto curto e letra grande: versículo + no máximo 2 frases curtas + pedido de Amém (35 a 45 palavras), com 1 a 3 trechos `==grifados==` em amarelo.
- Tradução católica, citação com vírgula (Salmo 4,9). Público católico: pode Nossa Senhora, santos, Anjo da Guarda. pt-BR sempre.

```json
{"nome": "2026-11-20-manha-salmo23", "saida": "shorts/2026-11", "estilo": "biblia-foto", "duracao": 20, "modelo": 2,
 "titulo_leitura": "Salmo 23,1", "texto": ["O Senhor é o meu pastor, ==nada me faltará==.", "..."], "particulas": "leve"}
```

O estilo `biblia` (página clara com grifo animado) continua disponível no gerador; exemplo em `specs/2026-11-06-manha.json`.

## Copy

- **Título:** gancho com 1 palavra em MAIÚSCULAS + emoji + versículo + `#shorts` (até 100 caracteres). Ex.: `Você pediu um sinal de DEUS? Reze esta oração 🙏 Salmo 51,12 #shorts`.
- **Descrição:** 1ª linha com urgência, versículo completo, "Escreva AMÉM...", "Deixe o nome de quem...", "Inscreva-se na Vox Dei...", 5 a 6 hashtags (#oração #oraçãocatólica #salmoX #catolicos #shorts).
- YouTube: `categoryId` "22", `madeForKids` false, `isAiGenerated` false. O Buffer NÃO define idioma nem tags: a thread de SEO corrige para pt-BR e põe as tags no lote noturno (aviso de 15/11).

## Formato novo: oração na íntegra (desde 12/11)

- Pedido da Helo (11/11) para quebrar o molde Bíblia: oração inteira rezada por voz calma, texto que acende palavra por palavra, fundo escuro com luz de vela, gancho "Pare um instante" no 1º quadro e CTA "escreva Amém". Cerca de 40 s.
- Gerador: `python3 scripts/make_oracao.py specs/<spec>.json` (exemplo: `specs/2026-11-12-manha-oracao.json`). Voz por `edge-tts` (`pip install edge-tts`), fica em `<saida>/voz/`. Render demora ~8 min.
- 1º vídeo: São Miguel Arcanjo, 12/11 7h. Ver o resultado antes de repetir o formato.

## Fila do Facebook (pedido da Helo, 19/11)
Ao AGENDAR qualquer Short (corte ou Bíblia no molde Fábio), acrescente uma linha em `/mnt/project-files/facebook/FILA-FACEBOOK.md`: arquivo mp4, título, link do YouTube (e data/hora). NÃO poste no Facebook: quem posta é a thread "Aquecer página do Facebook".

## Limite de uploads por dia (regra da Helo, 23/11/2026)
A cota diária da API do YouTube é de 10.000 pontos (zera ~5h de Brasília). Cada upload de vídeo custa 1.600 pontos; resposta a comentário, capa, tags e playlist custam 50. **No máximo 5 uploads por dia** pela API (somando Shorts, longos e cortes). Lotes grandes devem ser divididos em dois ou mais dias. Ver cota-api-youtube na memória do projeto.

## Título dos Bíblias das 7h (Mentor, 24/11)
Manter o molde Fábio e colocar "Escreva AMÉM" no TÍTULO (ex.: `Marcos 11,24 🙏 Escreva AMÉM`). Com isso o Marcos 11,24 teve 11,4 comentários/mil views contra 4,5 do Êxodo 14,14 (sem o pedido no título).

## Toda data vai para a agenda da Helo (regra permanente, 25/11/2026)
A Helo abre a agenda (https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw) todo dia. Sempre que você citar uma data à Helo (teste, prazo, revisão, algo que ela deve fazer, resultado que será lido), grave na mesma hora um doc em `plano` com `formato: "teste"`: doc_id `AAAA-MM-DD-teste-HHMM-<slug>`, campos `data`, `hora`, `titulo`, `etapa` ("marcado" ou "feito"), opcional `nota`. Passo a passo em /mnt/project-files/producao/AGENDA-YOUTUBE.md (seção "Testes e avisos com data"). Postagens do YouTube/Facebook/TikTok já entram pelos seus fluxos; esta regra cobre o resto.

> Atenção: não apagar nem renomear a branch `claude/project-thread-0fzddr` antes de 30/11/2026 19h30 (BRT). O Buffer baixa o vídeo do TikTok por link raw dela.
