# AI Service - Analisi dei Progressi dei Pazienti

Questo progetto fornisce un servizio per analizzare i dati di pazienti fisioterapici, con particolare attenzione al rilevamento di miglioramenti nei sintomi di dolore lombare. Si basa su **MongoDB**, **NLTK** e integra un'opzione di analisi con modelli AI (OpenAI GPT o Gemini, al momento commentati).

## Funzionalità principali

* Connessione a un database MongoDB per recuperare pazienti, appuntamenti e note cliniche.
* Analisi testuale in italiano con tokenizzazione, stemming e ricerca di parole chiave di miglioramento.
* Funzione di fallback AI (GPT o Gemini) per convalida di casi ambigui.
* Struttura modulare con funzioni riutilizzabili.

## Struttura del codice

* `get_db_client()`: connessione a MongoDB.
* `is_improvement()` e `extract_improvement_sentences()`: identificazione di frasi con miglioramenti.
* `ask_gpt()`: chiamata al modello GPT per analisi avanzata.
* `ask_gemini()`: chiamata al modello GPT per analisi avanzata.
* `AnalyzeResponse`: modello Pydantic per la risposta.
* `analyze_records()`: logica principale per l'analisi dei dati.

## Requisiti

* **Python 3.9+**
* Librerie principali:

  * `fastapi`
  * `pydantic`
  * `pymongo`
  * `nltk`
  * `openai` o `google.generativeai`
* MongoDB attivo (configurabile tramite variabili d'ambiente `MONGO_URI`, `DB_NAME`).

## Installazione

```bash
# Clona il repository
git clone <repo-url>
cd <repo-folder>

# Crea e attiva un virtual environment
python -m venv venv
source venv/bin/activate  # su Windows: venv\Scripts\activate

# Installa le dipendenze
pip install -r requirements.txt
```

## Esecuzione

1. Assicurarsi che MongoDB sia in esecuzione e popolato con i dati.
2. Impostare le variabili d'ambiente se necessario:

```bash
export MONGO_URI="mongodb://localhost:27017/"
export DB_NAME="FisioDB"
export OPENAI_API_KEY="<la-tua-chiave>"
```

3. Avviare lo script:

```bash
python main.py
```

4. Verranno stampati in console i pazienti che hanno saltato l'ultimo appuntamento ma mostrano miglioramenti.

## Diagramma dell'architettura
Il diagramma dell'architettura è disponibile al link https://excalidraw.com/#json=3TwzNoR9n5GIXdY9wqMZJ,SlednUdWRBp0dPJnv4xq2g

## Note

* Il progetto è pensato per l'analisi interna e didattica; non è destinato all'uso in produzione senza ulteriori misure di sicurezza e privacy.
* Alcune funzioni (es. Gemini) sono commentate in attesa di integrazione.
