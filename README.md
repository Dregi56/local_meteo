# 🌦️ Local Meteo
**Local_Meteo** è un'integrazione per **Home Assistant** che raccoglie dati meteo in tempo reale da diverse fonti e li rende disponibili come sensori unici. L'integrazione è progettata per l'Italia, con aggiornamento rapido e sensori affidabili.

---

## ⚡ Fonti dati
| Parametro | Fonte principale | Fallback |
|-----------|-----------------|----------|
| Pioggia istantanea | Open-Meteo (minutely 15 min) | — |
| Pioggia accumulata | ARPAV (stazione più vicina) | Open-Meteo |
| Temperatura | ARPAV | Open-Meteo |
| Umidità | ARPAV | Open-Meteo |
| Vento | ARPAV | Open-Meteo |
| Temperatura percepita | Open-Meteo | — |
| Punto di rugiada | Open-Meteo | — |
| Pressione | Open-Meteo | — |
| Raffiche vento | Open-Meteo | — |
| Indice UV | Open-Meteo | — |
| Visibilità | Open-Meteo | — |
| Copertura nuvolosa | Open-Meteo | — |
| Condizione cielo | `_compute_sky()` → combina pioggia + cloudcover | — |

> Nota: Temperatura, vento e umidità sono **dati locali** presi sempre dalla stazione ARPAV più vicina. Gli altri parametri provengono da Open-Meteo, gratuito e senza API key.

---

## 🛠️ Sensori disponibili
| Sensore | Unità | Descrizione |
|---------|-------|-------------|
| Temperatura | °C | Temperatura attuale dalla stazione ARPAV più vicina |
| Umidità | % | Umidità relativa dalla stazione ARPAV più vicina |
| Temperatura percepita | °C | Temperatura percepita (windchill/heat index) |
| Punto di rugiada | °C | Temperatura di rugiada |
| Pressione | hPa | Pressione atmosferica al livello del mare |
| Velocità vento | km/h | Vento dalla stazione ARPAV più vicina |
| Direzione vento | ° | Direzione del vento |
| Raffiche vento | km/h | Velocità massima delle raffiche |
| Pioggia | mm | Pioggia accumulata dalla stazione ARPAV più vicina |
| Pioggia istantanea | mm/h | Intensità pioggia aggiornata ogni 15 minuti |
| Indice UV | UV | Indice di radiazione ultravioletta |
| Visibilità | m | Visibilità in metri |
| Copertura nuvolosa | % | Percentuale di copertura nuvolosa |
| Condizione cielo | — | Calcolata combinando pioggia e copertura nuvolosa |

---

## ⚙️ Configurazione
1. Vai in **Home Assistant > Impostazioni > Dispositivi e Servizi > Aggiungi integrazione**
2. Cerca `Local Meteo`
3. Inserisci:
   - **Latitudine** (obbligatoria)
   - **Longitudine** (obbligatoria)

> L'integrazione legge automaticamente la posizione globale di Home Assistant e propone questi valori come default. È comunque possibile modificarli.

---

## ⏱️ Aggiornamento dati
- Tutti i sensori si aggiornano ogni **5 minuti**
- La pioggia istantanea usa i dati **minutely 15** di Open-Meteo (aggiornamento ogni 15 minuti)
- Temperatura, vento e umidità vengono sempre letti dalla **stazione ARPAV più vicina**, con fallback automatico su Open-Meteo in caso di errore

---

## 📂 Struttura repository
```
custom_components/
└── local_meteo/
    ├── icons/
    │   └── icon.png
    ├── __init__.py
    ├── manifest.json
    ├── config_flow.py
    ├── coordinator.py
    ├── const.py
    └── sensor.py
```
