import requests
from bs4 import BeautifulSoup
import pandas as pd

# URL do site
url = "https://futurodasaude.com.br/categoria/sua-saude/?utm_source=goads&utm_medium=search&utm_campaign=Branding&gad_source=1&gclid=CjwKCAjw1NK4BhAwEiwAVUHPUAOLvQW_8nJvpeNtAxdZ20zd9Sn-Dt789pFFBDlAFlo3arMAhPO4ZhoCmLoQAvD_BwE"

# Enviar solicitação GET
response = requests.get(url)

# Analisar o conteúdo da página com BeautifulSoup
soup = BeautifulSoup(response.content, 'html.parser')

# Extrair os títulos, links e resumos das notícias
titles = soup.find_all('a', class_='awb-custom-text-color awb-custom-text-hover-color')
summaries = soup.find_all('p')

# Criar uma lista para armazenar os dados
news_data = []

# Preencher a lista com os dados
for title, summary in zip(titles, summaries):
    news_title = title.get_text(strip=True)
    news_link = title['href']
    news_summary = summary.get_text(strip=True)
    news_data.append([news_title, news_link, news_summary])

# Criar um DataFrame com os dados
df = pd.DataFrame(news_data, columns=['Título', 'Link', 'Resumo'])

# Salvar o DataFrame em um arquivo CSV
csv_file_path = r'C:\Users\wande\OneDrive\INFNET\7. 6º Semestre\Projeto de Bloco\data\noticias.csv'
df.to_csv(csv_file_path, index=False)

print(f"Arquivo salvo em: {csv_file_path}")
