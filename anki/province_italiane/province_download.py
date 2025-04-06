import requests
from province_db import get_db
from tqdm import tqdm

liste = """\
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Agrigento
https://it.wikipedia.org/wiki/Provincia_di_Alessandria
https://it.wikipedia.org/wiki/Provincia_di_Ancona
https://it.wikipedia.org/wiki/Valle_d'Aosta
https://it.wikipedia.org/wiki/Provincia_di_Arezzo
https://it.wikipedia.org/wiki/Provincia_di_Ascoli_Piceno
https://it.wikipedia.org/wiki/Provincia_di_Asti
https://it.wikipedia.org/wiki/Provincia_di_Avellino
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Bari
https://it.wikipedia.org/wiki/Provincia_di_Barletta-Andria-Trani
https://it.wikipedia.org/wiki/Provincia_di_Belluno
https://it.wikipedia.org/wiki/Provincia_di_Benevento
https://it.wikipedia.org/wiki/Provincia_di_Bergamo
https://it.wikipedia.org/wiki/Provincia_di_Biella
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Bologna
https://it.wikipedia.org/wiki/Provincia_autonoma_di_Bolzano
https://it.wikipedia.org/wiki/Provincia_di_Brescia
https://it.wikipedia.org/wiki/Provincia_di_Brindisi
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Cagliari
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Caltanissetta
https://it.wikipedia.org/wiki/Provincia_di_Campobasso
https://it.wikipedia.org/wiki/Provincia_di_Caserta
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Catania
https://it.wikipedia.org/wiki/Provincia_di_Catanzaro
https://it.wikipedia.org/wiki/Provincia_di_Chieti
https://it.wikipedia.org/wiki/Provincia_di_Como
https://it.wikipedia.org/wiki/Provincia_di_Cosenza
https://it.wikipedia.org/wiki/Provincia_di_Cremona
https://it.wikipedia.org/wiki/Provincia_di_Crotone
https://it.wikipedia.org/wiki/Provincia_di_Cuneo
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Enna
https://it.wikipedia.org/wiki/Provincia_di_Fermo
https://it.wikipedia.org/wiki/Provincia_di_Ferrara
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Firenze
https://it.wikipedia.org/wiki/Provincia_di_Foggia
https://it.wikipedia.org/wiki/Provincia_di_Forl%C3%AC-Cesena
https://it.wikipedia.org/wiki/Provincia_di_Frosinone
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Genova
https://it.wikipedia.org/wiki/Provincia_di_Gorizia
https://it.wikipedia.org/wiki/Provincia_di_Grosseto
https://it.wikipedia.org/wiki/Provincia_di_Imperia
https://it.wikipedia.org/wiki/Provincia_di_Isernia
https://it.wikipedia.org/wiki/Provincia_dell'Aquila
https://it.wikipedia.org/wiki/Provincia_della_Spezia
https://it.wikipedia.org/wiki/Provincia_di_Latina
https://it.wikipedia.org/wiki/Provincia_di_Lecce
https://it.wikipedia.org/wiki/Provincia_di_Lecco
https://it.wikipedia.org/wiki/Provincia_di_Livorno
https://it.wikipedia.org/wiki/Provincia_di_Lodi
https://it.wikipedia.org/wiki/Provincia_di_Lucca
https://it.wikipedia.org/wiki/Provincia_di_Macerata
https://it.wikipedia.org/wiki/Provincia_di_Mantova
https://it.wikipedia.org/wiki/Provincia_di_Massa-Carrara
https://it.wikipedia.org/wiki/Provincia_di_Matera
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Messina
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Milano
https://it.wikipedia.org/wiki/Provincia_di_Modena
https://it.wikipedia.org/wiki/Provincia_di_Monza_e_della_Brianza
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Napoli
https://it.wikipedia.org/wiki/Provincia_di_Novara
https://it.wikipedia.org/wiki/Provincia_di_Nuoro
https://it.wikipedia.org/wiki/Provincia_di_Oristano
https://it.wikipedia.org/wiki/Provincia_di_Padova
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Palermo
https://it.wikipedia.org/wiki/Provincia_di_Parma
https://it.wikipedia.org/wiki/Provincia_di_Pavia
https://it.wikipedia.org/wiki/Provincia_di_Perugia
https://it.wikipedia.org/wiki/Provincia_di_Pesaro_e_Urbino
https://it.wikipedia.org/wiki/Provincia_di_Pescara
https://it.wikipedia.org/wiki/Provincia_di_Piacenza
https://it.wikipedia.org/wiki/Provincia_di_Pisa
https://it.wikipedia.org/wiki/Provincia_di_Pistoia
https://it.wikipedia.org/wiki/Provincia_di_Pordenone
https://it.wikipedia.org/wiki/Provincia_di_Potenza
https://it.wikipedia.org/wiki/Provincia_di_Prato
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Ragusa
https://it.wikipedia.org/wiki/Provincia_di_Ravenna
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Reggio_Calabria
https://it.wikipedia.org/wiki/Provincia_di_Reggio_Emilia
https://it.wikipedia.org/wiki/Provincia_di_Rieti
https://it.wikipedia.org/wiki/Provincia_di_Rimini
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Roma_Capitale
https://it.wikipedia.org/wiki/Provincia_di_Rovigo
https://it.wikipedia.org/wiki/Provincia_di_Salerno
https://it.wikipedia.org/wiki/Provincia_di_Sassari
https://it.wikipedia.org/wiki/Provincia_di_Savona
https://it.wikipedia.org/wiki/Provincia_di_Siena
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Siracusa
https://it.wikipedia.org/wiki/Provincia_di_Sondrio
https://it.wikipedia.org/wiki/Provincia_del_Sud_Sardegna
https://it.wikipedia.org/wiki/Provincia_di_Taranto
https://it.wikipedia.org/wiki/Provincia_di_Teramo
https://it.wikipedia.org/wiki/Provincia_di_Terni
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Torino
https://it.wikipedia.org/wiki/Libero_consorzio_comunale_di_Trapani
https://it.wikipedia.org/wiki/Provincia_autonoma_di_Trento
https://it.wikipedia.org/wiki/Provincia_di_Treviso
https://it.wikipedia.org/wiki/Provincia_di_Trieste
https://it.wikipedia.org/wiki/Provincia_di_Udine
https://it.wikipedia.org/wiki/Provincia_di_Varese
https://it.wikipedia.org/wiki/Citt%C3%A0_metropolitana_di_Venezia
https://it.wikipedia.org/wiki/Provincia_del_Verbano-Cusio-Ossola
https://it.wikipedia.org/wiki/Provincia_di_Vercelli
https://it.wikipedia.org/wiki/Provincia_di_Verona
https://it.wikipedia.org/wiki/Provincia_di_Vibo_Valentia
https://it.wikipedia.org/wiki/Provincia_di_Vicenza
https://it.wikipedia.org/wiki/Provincia_di_Viterbo
"""

pb = tqdm(total=liste.count("\n"))
with get_db() as data:
    for line in liste.splitlines():
        name = line.rsplit("/", 1)[-1]
        req = requests.get(f"https://it.wikipedia.org/w/api.php?action=query&format=json&prop=revisions&titles={name}&formatversion=2&rvprop=content&rvslots=*")
        text = req.json()["query"]["pages"][0]["revisions"][0]["slots"]["main"]["content"]
        data[name] = text
        pb.update(1)
