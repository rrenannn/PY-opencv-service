# Serviço de filtragem de fotos de vistoria

Aplicação web para receber um arquivo ZIP com fotos sequenciais de uma vistoria,
identificar imagens borradas com OpenCV e devolver somente as fotos aprovadas,
renomeadas e preservando a ordem do percurso.

O planejamento completo está em
[`docs/planejamento_do_sistema.md`](docs/planejamento_do_sistema.md).

## Fase atual: MVP

O primeiro marco deve entregar um fluxo completo e simples:

1. Receber e validar um arquivo `.zip`.
2. Extrair somente imagens suportadas, sem permitir caminhos inseguros no ZIP.
3. Ordenar as fotos de forma determinística pelo nome natural e usar metadados
   apenas como critério secundário.
4. Calcular a nitidez de cada imagem pela variância do Laplaciano.
5. Separar imagens aprovadas e descartadas com um limiar configurável.
6. Renomear as aprovadas (`foto_001.jpg`, `foto_002.jpg`, ...).
7. Gerar e disponibilizar um novo ZIP, junto de um resumo do processamento.

## Sequência sugerida de implementação

- Estruturar a aplicação FastAPI e criar um endpoint de saúde.
- Implementar o núcleo de processamento como funções independentes da API.
- Adicionar o endpoint de upload e download do resultado.
- Criar a interface web mínima de envio, progresso e resultado.
- Cobrir ordenação, ZIPs inválidos, formatos de imagem e filtragem com testes.
- Calibrar o limiar com fotos reais e documentar o valor inicial escolhido.
- Preparar container e configuração de implantação somente após validar o fluxo
  local de ponta a ponta.

## Decisões recomendadas para o MVP

- Python 3.12, FastAPI, Uvicorn, OpenCV headless e pytest.
- Imagens aceitas inicialmente: JPEG e PNG.
- Limites configuráveis para tamanho do ZIP, quantidade de arquivos e dimensões.
- Diretório temporário exclusivo por requisição e limpeza garantida ao final.
- Limiar de nitidez configurado por variável de ambiente, não fixado na lógica.
- Manifesto JSON ou CSV no ZIP de saída com nome original, novo nome, pontuação
  e decisão; isso facilita a calibração e a auditoria do resultado.

## Critério de conclusão da Fase 1

A fase estará concluída quando um usuário conseguir enviar um pacote real de
vistoria, receber o ZIP filtrado na ordem correta e entender, pelo resumo, quais
fotos foram removidas e por quê. O fluxo deve ter testes automatizados e não
deixar arquivos temporários após sucesso ou erro.

