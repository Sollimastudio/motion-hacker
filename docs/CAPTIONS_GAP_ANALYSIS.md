# Sol.IA Motion vs Captions — análise real do gap

Este documento registra, sem fantasia, o que o Captions tem hoje e o que o Sol.IA Motion ainda precisa modelar para se aproximar de um editor premium.

## Diagnóstico direto

O Sol.IA Motion atual é uma base técnica local: recebe vídeo, aplica templates simples via FFmpeg e exporta MP4 vertical.

O Captions é um produto completo de edição assistida por IA, com design system, modelos visuais, timeline, transcrição, legendas, cortes, templates e experiência de uso polida.

A diferença principal não é só tecnologia. É produto, design, UX, inteligência editorial e refinamento visual.

## O que o Captions tem que o Sol.IA ainda não tem

### 1. Design system visual

O Captions usa estilos consistentes: tipografia, sombras, caixas, contraste, espaçamento, cores e hierarquia visual. O Sol.IA ainda usa `drawtext` e caixas fixas via FFmpeg, o que deixa o visual duro e amador.

Necessário no Sol.IA:

- biblioteca de estilos;
- hierarquia tipográfica;
- presets visuais premium;
- posicionamento responsivo;
- componentes de legenda;
- overlays com estética consistente.

### 2. Timeline real de edição

O Captions edita por cenas, blocos e momentos do vídeo. O Sol.IA ainda trabalha com tempos fixos e templates rígidos.

Necessário no Sol.IA:

- criar timeline JSON interna;
- dividir vídeo por cenas;
- associar cada cena a texto, legenda, B-roll, zoom, produto e CTA;
- exportar a timeline para FFmpeg ou Remotion.

### 3. Transcrição automática

O Captions entende o vídeo porque transcreve a fala. O Sol.IA ainda depende de texto manual.

Necessário no Sol.IA:

- integrar Whisper local ou faster-whisper;
- gerar segmentos com timestamps;
- salvar transcrição em JSON;
- usar a transcrição como base da edição.

### 4. Legendas sincronizadas bonitas

O Captions tem legendas com ritmo, estilo e timing. O Sol.IA ainda simula legenda por blocos grandes.

Necessário no Sol.IA:

- legenda por frase;
- legenda por palavra no futuro;
- destaque de palavra-chave;
- contorno, sombra e fundo adaptativo;
- presets de legenda.

### 5. Corte de silêncio e ritmo

O Captions remove pausas, acelera o ritmo e deixa o vídeo mais assistível. O Sol.IA ainda não corta o vídeo com base em áudio/fala.

Necessário no Sol.IA:

- detectar silêncio com FFmpeg;
- remover pausas acima de um limite;
- cortar início morto;
- criar ritmo com cortes curtos;
- preservar frases completas para não cortar fala no meio.

### 6. B-roll e imagens de apoio

O Captions permite estilos e recursos visuais que enriquecem a cena. O Sol.IA começou a aceitar capa de produto, mas ainda não tem biblioteca de imagens nem lógica visual.

Necessário no Sol.IA:

- upload de múltiplas imagens;
- pasta de assets locais;
- seleção manual de B-roll;
- depois integração com banco de imagens;
- depois geração de imagens por IA;
- timeline alternando rosto, produto, imagem e texto.

### 7. Experiência de uso

O Captions é fácil: upload, estilo, criar vídeo. O Sol.IA ainda exige entendimento técnico, rodar local, lidar com terminal e esperar render sem preview fino.

Necessário no Sol.IA:

- tela de projetos;
- preview curto;
- botão abrir último vídeo;
- nomes de arquivos amigáveis;
- histórico visual;
- indicador de progresso;
- presets explicados em linguagem comum.

## O que dá para modelar no Sol.IA Motion

Quase tudo pode ser modelado, mas não tudo com FFmpeg puro do jeito atual.

### Dá para fazer com FFmpeg

- cortes;
- crop vertical;
- filtros;
- normalização de áudio;
- caixas e textos simples;
- overlay de imagens;
- concatenação;
- remoção de silêncio;
- legendas SRT/ASS.

### Fica ruim com FFmpeg puro

- animações sofisticadas;
- templates muito refinados;
- composição premium;
- edição visual parecida com app moderno;
- componentes complexos de legenda;
- previews interativos.

### Melhor caminho para visual premium

Usar FFmpeg para processamento pesado e Remotion/React para composição visual.

Arquitetura sugerida:

```text
Upload → Transcrição → Timeline JSON → Remotion renderiza composição visual → FFmpeg finaliza/otimiza MP4
```

## Roadmap correto daqui para frente

### Versão 0.4 — Timeline por roteiro

Objetivo: transformar texto manual em cenas.

Entregas:

- campo de roteiro manual;
- quebra em cenas;
- timeline JSON;
- legendas por blocos;
- nomes de saída amigáveis;
- botão para abrir último vídeo.

### Versão 0.5 — B-roll manual

Objetivo: permitir que a Sol suba imagens de apoio.

Entregas:

- upload de múltiplas imagens;
- template Você + Imagem;
- template Produto + Fala;
- template Gancho + B-roll + CTA.

### Versão 0.6 — Whisper local

Objetivo: o app ouvir o vídeo.

Entregas:

- faster-whisper;
- transcrição com timestamps;
- geração automática de roteiro;
- fallback para roteiro manual.

### Versão 0.7 — Corte de silêncio

Objetivo: remover pausas e começo morto.

Entregas:

- detectar silêncio;
- gerar lista de cortes;
- preservar frases completas;
- renderizar versão compacta.

### Versão 0.8 — Legendas estilo premium

Objetivo: aproximar de Captions/CapCut.

Entregas:

- legenda por frase;
- destaque de palavras;
- presets de legenda;
- sombras, contorno e caixas melhores;
- layout mobile-first.

### Versão 0.9 — Render visual moderno

Objetivo: sair do visual duro do FFmpeg.

Entregas:

- Remotion ou compositor visual equivalente;
- templates React;
- animações;
- barras, cards, molduras, stickers e elementos visuais.

## Conclusão

O Sol.IA Motion pode evoluir para algo útil, mas o caminho não é continuar empilhando tarjas no FFmpeg.

A próxima fase correta é criar um motor de timeline e depois migrar o visual para um compositor mais moderno. FFmpeg continua como motor de vídeo, mas não deve ser o responsável sozinho pelo design premium.
