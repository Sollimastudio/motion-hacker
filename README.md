# Sol.IA Motion Editor Local

Aplicativo local para editar vídeos curtos no próprio computador.

Esta versão foi pensada para uso pessoal: você roda localmente, sobe seus vídeos, coloca um texto de abertura e gera um MP4 vertical 1080×1920 para Reels, TikTok ou Shorts.

## O que já funciona

- Interface visual no navegador.
- Upload de vídeo.
- Fila de processamento local.
- Renderização com FFmpeg.
- Conversão para vídeo vertical 1080×1920.
- Texto de abertura nos primeiros 4 segundos.
- Download do vídeo final.

## O que ainda não faz

- Transcrição automática.
- Corte inteligente de silêncio.
- Legendas sincronizadas.
- Escolha automática dos melhores trechos.
- IA editorial.

Essas funções entram depois. Primeiro o app precisa abrir, receber vídeo e devolver vídeo. O resto é luxo — necessário, mas luxo.

## Instalação no computador

### 1. Instale o Python

Baixe em:

```text
https://www.python.org/downloads/
```

Durante a instalação, marque a opção **Add Python to PATH**.

### 2. Instale o FFmpeg

O FFmpeg é o motor que renderiza o vídeo.

No Windows, a forma mais simples é instalar pelo site oficial ou pelo Chocolatey.

No Mac:

```bash
brew install ffmpeg
```

No Linux:

```bash
sudo apt install ffmpeg
```

### 3. Baixe o repositório

```bash
git clone https://github.com/Sollimastudio/motion-hacker.git
cd motion-hacker
```

### 4. Instale as dependências

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Mac/Linux:

```bash
source .venv/bin/activate
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
3. Escreva um texto de abertura, por exemplo:

```text
Pare de chamar ausência de paz.
```

4. Escolha um estilo:
   - UGC Confessional: natural.
   - Retention Cut: mais contraste e força.
   - Premium Noir: editorial, escuro e mais sofisticado.
5. Clique em **Editar meu vídeo**.
6. Aguarde processar.
7. Clique em **Baixar vídeo pronto**.

## Onde ficam os arquivos

- Vídeos enviados: `uploads/`
- Vídeos prontos: `outputs/`

## Próxima fase

A próxima versão deve adicionar:

1. transcrição automática com Whisper local;
2. legenda automática;
3. corte de silêncio;
4. presets mais bonitos;
5. opção de escolher duração final;
6. capa automática.

## Observação importante

Este app roda localmente. Ele não publica nada, não manda seus vídeos para rede social e não precisa de login.
