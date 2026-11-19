<h1>
  <img src="https://raw.githubusercontent.com/Dregi56/Local_Meteo/main/custom_components/local_meteo/brand/icon.png" width="72" align="absmiddle" alt="Local Meteo">
  Local Meteo
</h1>

**Local Meteo** è un'integrazione per **Home Assistant** che raccoglie dati meteo in tempo reale da diverse fonti e li rende disponibili come sensori unici. È pensata per l'Italia, con aggiornamento rapido e la possibilità di scegliere la località e la stazione meteo ARPAV da cui leggere i dati locali.

---

## ⚡ Fonti dati e crediti

| Parametro | Fonte principale | Fallback |
|-----------|-----------------|----------|
| Temperatura | [ARPAV](https://www.arpa.veneto.it) (stazione scelta o più vicina) | [Open-Meteo](https://open-meteo.com/) |
| Umidità | Open-Meteo | — |
| Temperatura percepita | Open-Meteo | — |
| Punto di rugiada | Open-Meteo | — |
| Pressione | Open-Meteo | — |
| Vento (velocità e direzione) | Open-Meteo | — |
| Raffiche vento | Open-Meteo | — |
| Pioggia | Open-Meteo | — |
| Pioggia istantanea | Open-Meteo (dati ogni 15 minuti) | — |
| Indice UV | Open-Meteo | — |
| Visibilità | Open-Meteo | — |
| Copertura nuvolosa | Open-Meteo | — |
| Condizione cielo | `_compute_sky()` → combina pioggia e copertura nuvolosa | — |

> **Nota:** Open-Meteo è gratuito e non richiede API key. I dati ARPAV sono locali e provengono dalla stazione che scegli in fase di configurazione.
>
> **Copertura ARPAV:** ARPAV è l'agenzia regionale del **Veneto**, quindi i dati delle stazioni sono significativi per località in Veneto o vicine. In modalità automatica, se la stazione più vicina è a più di 30 km, i dati ARPAV vengono ignorati e restano solo quelli di Open-Meteo.

### 🙏 Crediti

- **Dati meteo e ricerca località**: [Open-Meteo.com](https://open-meteo.com/),
  licenza [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  *Weather data by [Open-Meteo.com](https://open-meteo.com/).*
- **Dati delle stazioni meteo**: ARPAV – Agenzia Regionale per la Prevenzione e
  Protezione Ambientale del Veneto, Dipartimento Regionale per la Sicurezza del Territorio
  ([www.arpa.veneto.it](https://www.arpa.veneto.it)), dati rilasciati con licenza
  [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.it).

<sub>Questo progetto non è affiliato, approvato o sponsorizzato da Open-Meteo né da ARPAV. I dati sono forniti "così come sono", senza garanzie su accuratezza o disponibilità.</sub>

---

## 🛠️ Sensori disponibili

| Sensore | Unità | Descrizione |
|---------|-------|-------------|
| Temperatura | °C | Temperatura attuale (stazione ARPAV, altrimenti Open-Meteo) |
| Umidità | % | Umidità relativa |
| Temperatura percepita | °C | Temperatura percepita (windchill / heat index) |
| Punto di rugiada | °C | Temperatura di rugiada |
| Pressione | hPa | Pressione atmosferica al livello del mare |
| Velocità vento | km/h | Velocità del vento |
| Direzione vento | ° | Direzione del vento |
| Raffiche vento | km/h | Velocità massima delle raffiche |
| Pioggia | mm | Precipitazione attuale |
| Pioggia istantanea | mm | Pioggia degli ultimi 15 minuti |
| Indice UV | UV | Indice di radiazione ultravioletta |
| Visibilità | m | Visibilità in metri |
| Copertura nuvolosa | % | Percentuale di copertura nuvolosa |
| Condizione cielo | — | Calcolata combinando pioggia e copertura nuvolosa |

I sensori che leggono dati ARPAV mostrano anche l'attributo `stazione_arpav` con il nome della stazione in uso.

---

## 📦 Installazione

### HACS (repository personalizzato)

1. In HACS apri il menu ⋮ → **Repository personalizzati**.
2. Aggiungi `https://github.com/Dregi56/Local_Meteo` con categoria **Integrazione**.
3. Cerca **Local Meteo**, scaricala e riavvia Home Assistant.

### Manuale

Copia la cartella `custom_components/local_meteo` nella cartella `custom_components` di Home Assistant e riavvia.

**Requisiti:** Home Assistant **2024.11** o successivo (per il pulsante *Configura*). L'icona nella pagina delle integrazioni richiede la versione **2026.3** o successiva.

---

## ⚙️ Configurazione

1. Vai in **Home Assistant > Impostazioni > Dispositivi e Servizi > Aggiungi integrazione**
2. Cerca `Local Meteo`
3. Nella finestra di configurazione hai due possibilità:
   * **Posizione di Home Assistant (predefinita)**: lascia il campo *Città / Paese* vuoto e conferma. Latitudine e longitudine vengono lette automaticamente dalla posizione di casa impostata in Home Assistant (la finestra te ne mostra i valori).
   * **Un'altra località**: scrivi il nome della città o del paese. Latitudine e longitudine vengono calcolate in automatico tramite la [Geocoding API di Open-Meteo](https://open-meteo.com/en/docs/geocoding-api).
4. Se esistono più località con lo stesso nome (ad esempio "San Martino"), ti viene chiesto di scegliere quella corretta da un elenco con comune, provincia e regione.
5. Scegli la **stazione meteo ARPAV**: vedi l'elenco delle stazioni più vicine con la distanza in km. Con **Automatica** viene usata la più vicina, ma puoi sceglierne una diversa se è più rappresentativa per la tua zona.

### Cambiare località o stazione

Dopo l'installazione puoi cambiarle da **Impostazioni > Dispositivi e Servizi > Local Meteo > Configura**: inserisci una nuova città, oppure lascia il campo vuoto per tornare alla posizione di casa di Home Assistant, poi scegli la stazione. L'integrazione si ricarica da sola.

> **Nota:** la posizione di Home Assistant viene letta al momento del salvataggio della configurazione. Se in seguito la modifichi in Home Assistant, apri **Configura**, lascia il campo vuoto e conferma per aggiornare l'integrazione.

---

## ⏱️ Aggiornamento dati

- Tutti i sensori si aggiornano ogni **5 minuti**.
- La pioggia istantanea usa i dati a **15 minuti** di Open-Meteo.
- Se una fonte non risponde, i sensori che dipendono da lei mantengono gli altri valori e il problema viene registrato nel log di Home Assistant.

---

## 📂 Struttura repository

```
custom_components/
└── local_meteo/
    ├── brand/
    │   └── icon.png
    ├── translations/
    │   ├── en.json
    │   └── it.json
    ├── __init__.py
    ├── arpav.py
    ├── config_flow.py
    ├── const.py
    ├── coordinator.py
    ├── manifest.json
    └── sensor.py
```

---

## 📄 Licenza

Rilasciato con licenza **MIT**: vedi il file [LICENSE](LICENSE).
