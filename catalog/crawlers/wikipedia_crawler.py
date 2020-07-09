import requests
from bs4 import BeautifulSoup
import json
# url = "https://en.wikipedia.org/wiki/Aravind_Adiga"
# url = "https://en.wikipedia.org/wiki/Khaled_Hosseini"
# url = "https://en.wikipedia.org/wiki/Tina_Fey"
# url = "https://en.wikipedia.org/wiki/Brian_Greene"
# url = "https://en.wikipedia.org/wiki/The_Fabric_of_the_Cosmos"
url = "https://en.wikipedia.org/wiki/The_White_Tiger_(Adiga_novel)"

html_page = requests.get(url)
soup = BeautifulSoup(html_page.text, 'lxml')
table = soup.table
data = {}
table_rows = table.find_all("tr")
for tr in table_rows:
    td = tr.find_all("td")
    th = tr.find_all("th")
    data[" ".join([h.text for h in th]).replace("\xa0"," ")] = ", ".join([d.text for d in td]).replace("\xa0"," ")
print(json.dumps(data))
