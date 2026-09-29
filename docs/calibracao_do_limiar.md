# Calibração do limiar de nitidez

O valor `100` é apenas um ponto de partida. A pontuação da variância do
Laplaciano muda conforme resolução, câmera, compressão, iluminação e conteúdo da
foto. O limiar final deve ser escolhido com imagens reais de vistoria.

## 1. Montar uma amostra representativa

Separe pelo menos 100 fotos, preferencialmente de mais de uma vistoria. Inclua:

- ambientes claros e escuros;
- superfícies lisas, que naturalmente têm poucos detalhes;
- fotos próximas e panorâmicas;
- imagens claramente nítidas, levemente tremidas e inutilizáveis;
- arquivos de todas as câmeras e resoluções usadas na operação.

Mantenha um segundo pacote de fotos fora da calibração. Ele será usado somente
na validação final.

## 2. Obter as pontuações

Inicie a aplicação e processe o ZIP com limiar `0`. Dessa forma, todas as imagens
válidas estarão no resultado e o arquivo `manifesto.csv` conterá a pontuação de
nitidez de cada uma.

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Abra `http://127.0.0.1:8000`, escolha o pacote e informe `0` no campo de limiar.

## 3. Classificar manualmente

Adicione ao manifesto uma coluna chamada `classificacao_manual` e marque cada
imagem como:

- `nitida`: pode entrar no relatório final;
- `borrada`: deve ser removida;
- `duvida`: requer revisão humana.

Essa decisão humana é a referência para avaliar o algoritmo.

## 4. Escolher o valor

Ordene a planilha pela coluna `nitidez` e procure a região que melhor separa as
fotos `borrada` das fotos `nitida`. Teste valores próximos dessa região na
interface, por exemplo `50`, `75`, `100`, `125` e `150`.

Priorize não remover uma foto válida. Para uma vistoria, uma falsa remoção tende
a ser mais prejudicial do que deixar uma foto levemente borrada para revisão.
Se houver muita sobreposição entre as classes, use um limiar conservador e
considere uma faixa de revisão manual em uma fase posterior.

## 5. Validar sem reajustar

Processe o segundo pacote usando o valor escolhido e confira:

1. se a ordem foi preservada;
2. se nenhuma foto necessária foi removida;
3. se as imagens claramente inutilizáveis foram descartadas;
4. se os nomes ficaram sequenciais;
5. se o manifesto corresponde ao conteúdo do ZIP.

Não reajuste o limiar usando esse segundo pacote. Se o resultado não for bom,
amplie a amostra original, calibre novamente e valide com um novo conjunto.

## 6. Configurar o serviço

Depois da validação, registre o valor no ambiente:

```bash
SHARPNESS_THRESHOLD=100
```

O usuário ainda poderá substituir esse valor em um processamento específico por
meio do campo de limiar da interface.

