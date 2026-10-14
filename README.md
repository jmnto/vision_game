# ORCHARD — o pomar do robô Zé

Jogo local com **inferência YOLO real**, dez fases, fotografias sintéticas, pegadinhas visuais, sequência de acertos, animações e comentários do robô Zé.

## Jogar

```bash
./start.sh
```

Abra **http://127.0.0.1:8000**. Outra porta: `./start.sh --port 8080`. No Windows, use Python 3.12 e execute `start.bat`.

O modelo **`models/yolov8n.pt` e o frontend compilado estão incluídos**. Não precisa treinar, usar API, GPU ou instalar Node.js para jogar. Em uma máquina nova, a instalação inicial das dependências Python precisa de internet. Python 3.12 recomendado; `uv` é opcional. O ambiente `.venv` deste workspace já está preparado.

- **Analisar e colher** ou **Espaço**: executa uma leitura do cenário atual.
- **Colheita automática**: executa outra leitura 2,3 segundos após a anterior terminar; pode ser pausada e para ao concluir a fase ou sair do pomar. Não avança fases sozinha.
- **Som**: efeitos opcionais, desligados por padrão. Animações respeitam a preferência de movimento reduzido.
- **Confiança**: ajuste o limiar antes de cada leitura, inclusive no modo automático.
- **Novo jogo**: reinicia a campanha. As sessões ficam em memória; recarregar a página começa uma nova campanha.

A primeira leitura pode demorar mais porque carrega os pesos. Ao terminar, baixe o relatório JSON para guardar os resultados.

## Dez fases

| Fase | Frutas reais | Desafio |
|---|---:|---|
| Bom dia, pomar! | 8 maçãs | Luz clara e frutas grandes |
| Laranja é o novo desafio | 9 laranjas | Outra classe e outro enquadramento |
| Cadê a maçã? | 12 maçãs | Frutas pequenas, folhas e sombra |
| Hora extra no pomar | 10 laranjas | Pouca luz e ruído |
| Salada de algoritmos | 14 mistas | Maçãs e laranjas juntas |
| O pomar de plástico | 6 maçãs | Maçãs de plástico e vela de laranja |
| Natal fora de época | 6 mistas | Enfeites natalinos e frutas falsas |
| A liga das laranjas | 8 laranjas | Bolas de basquete e outras iscas |
| A feira dos impostores | 8 mistas | Seis iscas, quatro tipos e sombra |
| A grande pegadinha | **0** | Só decoração: saber não colher |

As primeiras nove fases terminam quando todas as frutas forem colhidas ou após cinco leituras. A final exige **uma leitura**, mesmo sem frutas, e testa a capacidade de não gerar falsos positivos.

## Pontuação e pegadinhas

**+100 por fruta correta; −40 por falso positivo.** O acerto exige a classe correta e IoU ≥ 0,40 com uma fruta real ainda presente. O pareamento é um a um, em ordem de confiança. Duplicatas e classes de fruta incorretas são penalizadas. Frutas não detectadas valem zero. Pontuação perfeita: **8.100**.

Somente previsões `apple`/`orange` (após aplicação de aliases) são tentativas de colheita. Reconhecer corretamente uma bola como `sports ball` não é erro: outras classes são ignoradas, com zero pontos e fora do cálculo de precisão. Reconhecê-la como `orange` é falso positivo e custa 40 pontos.

Iscas têm anotações independentes e **não desaparecem nem rendem pontos**. Se o modelo insistir em colher a mesma isca em outra leitura, perde pontos novamente. O jogo não injeta previsões falsas: as confusões vêm do detector. Um modelo especializado pode evitar as pegadinhas.

A sequência conta frutas corretas consecutivas na ordem de confiança; um falso positivo a zera. O recorde permanece na campanha. É um indicador visual, **sem multiplicador de pontos**, para manter comparações entre modelos. O relatório inclui motivos de erro, nome da isca, sequência e totais por fase.

## Usar seus pesos

1. Copie um modelo de detecção Ultralytics YOLO `.pt` confiável para `models/`, por exemplo `best.pt`.
2. Entre em **Laboratório → Atualizar lista de modelos**.
3. Volte ao pomar e selecione o modelo.

Use classes `apple` e `orange`. Plurais em inglês são normalizados. Para outros nomes, crie `models/best.json`:

```json
{"ripe_apple": "apple", "maca": "apple", "laranja": "orange"}
```

As chaves correspondem aos nomes do checkpoint em minúsculas. Os IDs de classe vêm do próprio modelo. Alterações nos pesos com o mesmo nome também são detectadas. ONNX, Darknet `.weights`, modelos somente de classificação, pose e OBB não são suportados. Novas arquiteturas podem exigir atualizar o Ultralytics.

## Limites da simulação

É um simulador **2D de composições fotográficas sintéticas**, não uma fazenda 3D nem um benchmark de câmera real. O cenário, as frutas e as iscas foram gerados como imagens. As frutas usam sprites com alpha e desaparecem pela remoção da camada. O detector recebe apenas a imagem, nunca as coordenadas das anotações. A inferência usa CPU e resolução de 960 pixels.

Os layouts são determinísticos para comparação. Texturas repetidas, iluminação controlada e frutas artificiais não representam toda a variabilidade de um pomar real. Não simulamos profundidade, movimento de braço robótico, maturação ou física da colheita.

## Desenvolvimento e verificação

```bash
npm --prefix frontend install
npm --prefix frontend run build
# Com o servidor Python rodando separadamente:
npm --prefix frontend run dev
.venv/bin/python -m unittest discover -s tests -v
# Campanha completa com o detector real:
.venv/bin/python scripts/benchmark.py --confidence 0.5
```

Node.js 22.12+ para desenvolvimento. `game.py` contém o renderizador, anotações, detector e regras; `server.py` fornece o serviço em `127.0.0.1`; `frontend/src/` contém a interface React; `assets/` contém a arte e `models/` os pesos substituíveis.

O backend não consome leitura nem pontos se a inferência falhar. Mantenha o terminal aberto enquanto joga. A prévia Vite encaminha requisições para a porta 8000 por padrão.

## Fontes e licenças

Pesos: [release oficial Ultralytics](https://github.com/ultralytics/assets/releases/download/v8.3.0/yolov8n.pt), com checksum em `models/SHA256SUMS`. [Documentação YOLOv8](https://docs.ultralytics.com/models/yolov8/) e [classes COCO](https://docs.ultralytics.com/datasets/detect/coco/).

Ultralytics e seus modelos seguem os termos [AGPL-3.0 / licença empresarial](https://www.ultralytics.com/license). As dependências frontend mantêm suas licenças. Imagens produzidas com a ferramenta integrada de geração de imagens; prompts em `docs/art-prompts.md`.
