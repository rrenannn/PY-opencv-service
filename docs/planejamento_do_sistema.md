# Planejamento: Sistema de Filtragem de Fotos de Vistoria

## 1. Visão Geral do Projeto
O objetivo deste sistema é otimizar o fluxo de trabalho de vistorias de engenharia. O usuário fará o upload de um arquivo `.zip` contendo fotos sequenciais de um imóvel. O sistema deverá identificar e remover automaticamente fotos borradas/tremidas, preservando rigorosamente a ordem cronológica do "caminho" feito dentro da casa, e devolver um novo arquivo processado.

## 2. Fases do Projeto

### Fase 1: MVP - Filtragem e Manutenção de Ordem (Foco Atual)
Nesta fase, construiremos a base do serviço através de uma aplicação Web simples.

*   **Entrada:** Arquivo `.zip` contendo as fotos brutas.
*   **Processamento Principal:**
    1.  **Extração e Ordenação:** Extrair os arquivos e ordená-los pelo nome ou data de criação para garantir que o "caminho da vistoria" não se perca.
    2.  **Análise de Nitidez:** Utilizar OpenCV (Variância do Laplaciano) para calcular a nitidez de cada imagem.
    3.  **Filtragem:** Descartar imagens cuja pontuação de nitidez caia abaixo de um limiar predefinido (threshold).
    4.  **Reindexação:** Renomear as fotos aprovadas em uma nova sequência lógica (ex: `foto_01.jpg`, `foto_02.jpg`) para que não fiquem buracos na numeração devido às fotos excluídas.
*   **Saída:** Um novo arquivo `.zip` contendo apenas as fotos nítidas e na ordem correta, pronto para download.

### Fase 2: Geração de Relatório Word (.docx) (Futuro)
Após a definição da formatação pelo cliente, o sistema passará a gerar o documento final para edição.

*   **Entrada:** Lista de fotos nítidas e ordenadas aprovadas na Fase 1.
*   **Processamento Principal (Geração do Documento):**
    *   Utilizar a biblioteca `python-docx` para criar o documento.
    *   Inserir as fotos numeradas.
    *   **Regra de Paginação:** Distribuir exatamente 6 fotos por página.
    *   **Regra de Finalização:** Aplicar a lógica condicional para a última página (múltiplos de 6 ou terminar com 4 fotos, evitando páginas com apenas 2 fotos).
*   **Saída:** Arquivo `.docx` formatado e editável.

## 3. Arquitetura e Stack Tecnológico (Opção 1 - Web App)

*   **Backend:** Python com **FastAPI** (leve, rápido e excelente para lidar com uploads e processamento assíncrono).
*   **Processamento de Imagem:** **OpenCV** (`cv2`).
*   **Frontend:** HTML/CSS e JavaScript puros (Interface simples de arrastar e soltar o `.zip` e um botão de "Processar").
*   **Manipulação de Arquivos:** Bibliotecas nativas do Python (`zipfile`, `os`, `shutil`).
*   **Infraestrutura (Sugestão):** Hospedagem em serviços em nuvem gratuitos ou de baixo custo como Render, Railway ou Google Cloud Run.

## 4. Próximos Passos Imediatos
1.  Criar a estrutura inicial do backend em FastAPI.
2.  Implementar a lógica de recebimento e extração do `.zip`.
3.  Desenvolver o script do OpenCV garantindo a leitura sequencial dos arquivos.
4.  Testar o limiar de nitidez com um pacote real de fotos de vistoria para calibrar o algoritmo.