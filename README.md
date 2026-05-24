# Sol.IA Motion / UGC Cut

Aplicativo local para editar vídeos curtos no próprio computador.

Esta versão é uma base funcional: você roda localmente, sobe seus vídeos, coloca textos, opcionalmente adiciona capa/imagem de produto e gera um MP4 vertical para Reels, TikTok ou Shorts.

## Diagnóstico honesto

O app já renderiza vídeos, mas ainda não compete visualmente com Captions, CapCut ou editores premium.

Hoje ele é um motor local com templates simples. Para virar um editor excelente, precisa evoluir em três frentes:

1. timeline visual por cenas;
2. transcrição/legenda automática;
3. sistema visual premium com templates melhores.

## O que já funciona

- Interface visual no navegador.
- Upload de vídeo.
- Upload opcional de imagem/capa de produto.
- Campo de roteiro manual/texto aproximado do vídeo.
- Fila de processamento local.
- Renderização com FFmpeg.
- Conversão para vídeo vertical.
- Templates simples:
  - Gancho Cinemático UGC;
  - Produto + Autoridade;
  - Tela dividida UGC;
  - Noir premium.
- Blocos de texto/legenda simulada a partir do roteiro manual.
- Download do vídeo final.

## O que ainda não faz bem

- Transcrição automática com Whisper.
- Corte inteligente de silêncio.
- Legendas sincronizadas por palavra.
- Escolha automática dos melhores trechos.
- B-roll automático.
- Busca em bancos de imagem.
- Imagens geradas por IA dentro do fluxo.
- Animações sofisticadas estilo Captions.
- Timeline editável.
- Preview visual refinado.

## Limitação atual

O app usa FFmpeg para aplicar textos e overlays. FFmpeg é excelente para processar vídeo, cortar, converter e renderizar, mas não é o melhor caminho para criar visual premium sozinho.

Para competir visualmente com Captions, o caminho recomendado é:

```text
Upload → transcrição/roteiro → timeline JSON → composição visual premium → render final
```

Provável stack visual futura:

```text
FFmpeg + Remotion/React
```

## Documentação de produto

Foi adicionada uma análise específica sobre o gap entre Captions e Sol.IA Motion:

```text
docs/CAPTIONS_GAP_ANALYSIS.md
```

Ela explica o que o Captions tem, o que dá para modelar, o que falta e qual roadmap seguir.

## Instalação no computador

### 1. Instale o Python

Baixe em:

```text
https://www.python.org/downloads/
```

### 2. Instale o FFmpeg

No Mac:

```bash
brew install ffmpeg
```

No Linux:

```bash
sudo apt install ffmpeg
```

No Windows, instale pelo site oficial do FFmpeg ou Chocolatey.

### 3. Baixe o repositório

```bash
git clone https://github.com/Sollimastudio/motion-hacker.git
cd motion-hacker
```

### 4. Instale as dependências

```bash
python -m venv .venv
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Depois:

```bash
pip install -r requirements.txt
```

### 5. Rode o app

```bash
uvicorn main:app --reload
```

Abra no navegador:

```text
http://127.0.0.1:8000
```

## Como usar

1. Clique em **Vídeo bruto**.
2. Escolha um vídeo do seu computador.
3. Opcionalmente, envie uma imagem/capa do produto.
4. Escolha um modelo.
5. Preencha:
   - frase inicial;
   - frase do meio;
   - CTA final;
   - texto aproximado do vídeo/roteiro manual.
6. Escolha a duração.
7. Clique em **Editar meu vídeo**.
8. Aguarde processar.
9. Clique em **Baixar vídeo pronto**.

## Onde ficam os arquivos

- Vídeos enviados: `uploads/`
- Imagens/capas: `assets/`
- Textos temporários: `text_assets/`
- Vídeos prontos: `outputs/`

## Roadmap realista

### 0.4 — Timeline por roteiro

- Transformar roteiro manual em cenas.
- Gerar timeline JSON.
- Usar timeline para posicionar textos, blocos e CTA.
- Melhorar nomes de arquivos e histórico.

### 0.5 — B-roll manual

- Upload de múltiplas imagens.
- Alternância entre rosto, imagem e produto.
- Templates de vídeo com apoio visual.

### 0.6 — Whisper local

- Transcrição automática.
- Timestamps por frase.
- Roteiro automático a partir do áudio.

### 0.7 — Corte de silêncio

- Detectar pausas.
- Remover espaços mortos.
- Preservar frases completas.

### 0.8 — Legendas premium

- Legenda por frase.
- Destaque de palavras.
- Presets visuais de legenda.

### 0.9 — Compositor visual moderno

- Migrar templates premium para Remotion/React ou equivalente.
- Animações, cards, motion graphics e composição mais bonita.

## Observação importante

Este app roda localmente. Ele não publica nada, não envia seus vídeos para redes sociais e não precisa de login.

Ele ainda é um projeto em construção. Para produção profissional imediata, use Captions/CapCut enquanto o Sol.IA evolui.
