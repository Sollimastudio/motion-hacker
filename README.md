# Sol.IA Motion Planner / UGC Cut

Aplicativo local para planejar e renderizar vídeos curtos no próprio computador.

## Estado real

O projeto já roda localmente, recebe vídeo, gera plano por cenas, renderiza com FFmpeg e exporta MP4 vertical.

Ele **ainda não compete visualmente com Captions ou CapCut**. Hoje ele é uma fundação técnica + um primeiro cérebro editorial. O visual ainda precisa evoluir muito.

## O que já funciona

- Interface visual no navegador.
- Upload de vídeo.
- Upload opcional de imagem/capa de produto.
- Campo de roteiro manual/texto aproximado do vídeo.
- Geração de plano por cenas via endpoint `/plan`.
- Cenas com função editorial:
  - GANCHO;
  - DOR;
  - VIRADA;
  - PRODUTO;
  - CTA.
- Renderização com FFmpeg.
- Conversão para vídeo vertical.
- Download do vídeo final.
- Acesso ao último vídeo por `/latest`.
- Acesso ao último plano JSON por `/latest-plan`.
- Salvamento do último vídeo em `outputs/ULTIMO_SOLIA_EDITADO.mp4`.
- Salvamento do último plano em `outputs/ULTIMO_PLANO_SOLIA.json`.

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

## Diagnóstico honesto

O app usa FFmpeg para aplicar textos, caixas e overlays. FFmpeg é excelente para processar vídeo, cortar, converter e renderizar, mas não é o melhor caminho sozinho para criar visual premium.

Para chegar perto do Captions, o produto precisa evoluir para:

```text
Upload → transcrição/roteiro → timeline JSON → composição visual premium → render final
```

Caminho provável:

```text
FFmpeg + Remotion/React
```

FFmpeg continua como motor técnico. Remotion/React entra para criar templates bonitos, animações, cards, transições e motion graphics.

## Como instalar

### 1. Baixar o repositório

```bash
git clone https://github.com/Sollimastudio/motion-hacker.git
cd motion-hacker
```

### 2. Criar ambiente Python

```bash
python -m venv .venv
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\\Scripts\\activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Instalar FFmpeg

Mac:

```bash
brew install ffmpeg
```

Linux:

```bash
sudo apt install ffmpeg
```

### 5. Rodar o app

```bash
uvicorn main:app --reload
```

Abrir:

```text
http://127.0.0.1:8000
```

## Como usar

1. Escolha o vídeo bruto.
2. Opcionalmente, envie uma imagem/capa de produto.
3. Escolha o modelo.
4. Preencha gancho, frase de sustentação e CTA.
5. Cole o texto aproximado do vídeo.
6. Clique em **Gerar plano de edição**.
7. Confira a timeline por cenas.
8. Clique em **Renderizar vídeo**.
9. Baixe o vídeo pronto.

## Arquivos importantes

- Vídeos enviados: `uploads/`
- Imagens/capas: `assets/`
- Textos temporários: `text_assets/`
- Vídeos prontos: `outputs/`
- Último vídeo: `outputs/ULTIMO_SOLIA_EDITADO.mp4`
- Último plano: `outputs/ULTIMO_PLANO_SOLIA.json`

## Roadmap realista

### 0.4.2 — Storyboard exportável

- Gerar storyboard em Markdown.
- Sugerir B-roll/imagens por cena.
- Sugerir direção de corte por cena.
- Criar plano que também sirva para editar no Captions/CapCut.

### 0.5 — Whisper local

- Transcrever vídeo automaticamente.
- Preencher o roteiro sem a usuária precisar colar texto.
- Gerar cenas a partir da fala real.

### 0.6 — Corte de silêncio

- Detectar pausas.
- Remover espaços mortos.
- Preservar frases completas.

### 0.7 — Legendas premium

- Legenda por frase.
- Destaque de palavras.
- Presets visuais de legenda.

### 0.8 — B-roll e imagens

- Upload de múltiplas imagens.
- Alternância entre rosto, imagem, produto e CTA.
- Futuro: banco de imagens ou geração por IA.

### 0.9 — Compositor visual moderno

- Migrar templates premium para Remotion/React ou equivalente.
- Animações, cards, motion graphics e composição mais bonita.

## Recomendação prática

Para produção profissional imediata, use Captions/CapCut enquanto o Sol.IA evolui.

Para desenvolvimento do produto, siga a ordem:

```text
Planejamento por cenas → Storyboard → Whisper → Corte de silêncio → Legendas premium → B-roll → Remotion
```
