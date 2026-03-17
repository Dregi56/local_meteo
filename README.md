# 🌦️ Local Meteo

# Local_Meteo - Integrazione Home Assistant

**Local_Meteo** è un’integrazione per **Home Assistant** che raccoglie dati meteo in tempo reale da diverse fonti e li rende disponibili come sensori unici. L’integrazione è progettata per l’Italia, con aggiornamento rapido e sensori affidabili.

---

## ⚡ Fonti dati

| Parametro | Fonte principale | Fallback |
|-----------|-----------------|----------|
| Pioggia istantanea | Protezione Civile (radar DPC) | ARPAV (stazione più vicina) |
| Pioggia accumulata | ARPAV (stazione più vicina) | Open-Meteo |
| Temperatura | ARPAV | Open-Meteo |
| Umidità | ARPAV | Open-Meteo |
| Vento | ARPAV | Open-Meteo |
| Condizione cielo | `_compute_sky()` → combina pioggia radar + cloudcover forecast | - |

> Nota: La temperatura, vento e umidità sono **dati locali sensibili** e vengono presi sempre dalla stazione più vicina. La pioggia istantanea utilizza il radar DPC per automazioni realtime.

---

## 🛠️ Sensori disponibili

| Sensore | Unità | Descrizione |
|---------|------|------------|
| Temperatura | °C | Temperatura attuale dalla stazione più vicina |
| Umidità | % | Umidità relativa dalla stazione più vicina |
| Velocità vento | km/h | Vento dalla stazione più vicina |
| Direzione vento | ° | Direzione del vento dalla stazione più vicina |
| Pioggia | mm | Pioggia accumulata dalla stazione più vicina |
| Pioggia istantanea | mm/h | Pioggia in tempo reale dal radar DPC |
| Condizione cielo | string | Calcolata combinando pioggia radar + forecast cloudcover |

---

## ⚙️ Configurazione

1. Vai in **Home Assistant > Impostazioni > Dispositivi e Servizi > Aggiungi integrazione**  
2. Cerca `Local Meteo`  
3. Inserisci:

   - **Latitudine** (obbligatoria)  
   - **Longitudine** (obbligatoria)  

> L’integrazione legge automaticamente la posizione globale di Home Assistant e propone questi valori come default. È comunque possibile modificarli.

---

## ⏱️ Aggiornamento dati

- La pipeline aggiorna tutti i sensori ogni **5 minuti**  
- La pioggia istantanea (radar DPC) è il dato più realistico per automazioni in tempo reale  
- Le altre grandezze (temperatura, vento, umidità) vengono aggiornate dalla stazione più vicina e dai dati forecast come fallback.

---

## 📂 Struttura repository
