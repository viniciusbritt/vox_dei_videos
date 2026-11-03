# Shorts da Vox Dei no TikTok

Todo dia às **02h40 (Brasília)** os 3 Shorts do dia (7h, 12h e 20h), que o agente das 5h03 já produziu na véspera, são agendados também no **TikTok**, pelo **TikTok Studio no navegador** (não pelo Buffer). Pedido da Helo em 03/11/2026, que autorizou fazer isso todo dia sem aprovação.

## Passo a passo

1. Abra `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/specs/` (ou `git pull`) e pegue os 3 specs de **hoje**: `AAAA-MM-DD-manha.json`, `-meiodia.json` e `-noite.json`. O campo `nome` diz o arquivo do vídeo: `shorts/AAAA-MM/<nome>.mp4`.
   - Se algum vídeo de hoje não existir, agende só os que existem e avise a Helo do que faltou.
2. Baixe cada vídeo: `https://raw.githubusercontent.com/viniciusbritt/vox_dei_videos/main/shorts/AAAA-MM/<nome>.mp4`.
3. Abra `https://www.tiktok.com/tiktokstudio/upload` no navegador onde a conta da Vox Dei já está logada. Se pedir login ou captcha, pare e avise a Helo (não tente contornar).
4. Antes de subir, confira em `https://www.tiktok.com/tiktokstudio/content` se o Short de hoje já não está agendado (para não duplicar se a tarefa rodar duas vezes).
5. Para cada vídeo:
   - Suba o arquivo.
   - **Descrição**: cole o texto montado pelas regras abaixo.
   - **Capa**: escolha o quadro final (com a oração inteira na tela).
   - **Quando publicar → Agendar**: hoje às **07:00**, **12:00** ou **20:00** (horário de Brasília; o TikTok aceita de 15 min a 10 dias à frente).
   - Quem pode ver: Todos. Comentários, Dueto e Costura: ligados.
   - Selo **Conteúdo gerado por IA**: só se o vídeo tiver cena realista feita por IA (os cartões de oração atuais não precisam, igual ao YouTube).
   - Clique em **Agendar** e confirme que aparece em Conteúdo como agendado.
6. Atualize a agenda (https://claude.ai/artifact/6pfcJwkDWtaFv9KspiVxVw), coleção `plano`, docs `AAAA-MM-DD`, `AAAA-MM-DD-meiodia` e `AAAA-MM-DD-noite`: grave `tiktok: "agendado"`, `tiktokHora` e `tiktokLegenda` (use `update`, sem apagar os outros campos).
7. Mande à Helo um aviso curto: o que foi agendado e a que horas, ou o que falhou.

## Descrição que mais converte no TikTok

O TikTok funciona como buscador: a 1ª linha é o "título" e precisa ter as palavras que as pessoas pesquisam (oração, Deus, Jesus, Salmo, cura, proteção...). Total de 150 a 300 caracteres.

```
<Gancho do vídeo com a palavra em destaque em MAIÚSCULAS> 🙏 <palavra-chave de busca: "Oração da manhã" / "Oração do meio-dia" / "Oração da noite"> | <Versículo>
Não passe sem rezar. Escreva AMÉM e marque quem precisa receber esta oração.
#oração #oraçãodanoite #católico #fé #deus #jesus #salmo<número> #fyp
```

- **1ª linha**: o gancho do vídeo + palavra de busca + versículo (com vírgula: Salmo 4,9). Ex.: `Hoje o Senhor tem uma CURA para você 🙏 Oração da manhã pela cura | Jeremias 17,14`.
- **2ª linha (CTA)**: varie entre "Escreva AMÉM e…", "Marque quem precisa…", "Salve para rezar de novo…" e "Compartilhe com quem você ama…". Salvar e compartilhar pesam muito no alcance do TikTok.
- **Hashtags**: de 5 a 8, no fim. Sempre `#oração #católico #fé`; mais 2 ou 3 do tema (`#oraçãodamanhã`, `#oraçãodanoite`, `#cura`, `#família`, `#nossasenhora`, `#salmo91`, `#ansiedade`, `#jesus`, `#deus`); e uma de alcance (`#fyp` ou `#paravocê`). Não use `#shorts` no TikTok.
- Nada de link nem "inscreva-se" (no TikTok é "Siga a Vox Dei para rezar todo dia", se couber).
- Não repita a mesma descrição de outro dia: confira as últimas legendas no TikTok Studio.
