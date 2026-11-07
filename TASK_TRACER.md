# Task Tracer — Refactoring & Evoluzione Scenografia (`antigravity`)

Questo file traccia in tempo reale lo stato di avanzamento dei Task e Sotto-Task previsti dal Piano di Implementazione sul branch `antigravity`.
Le attività sono ordinate secondo una sequenza **Bottom-Up sinergica** (5 Fasi) per azzerare conflitti e doppie lavorazioni.

---

## 📊 Riepilogo Avanzamento

**Progresso Globale:** `10 / 17` step operativi completati (**59%**)

```text
[██████████░░░░░░░] 59% (10/17 Task & Sotto-Task)
```

- **Branch attivo**: `antigravity`
- **Task principali**: `7 / 11`
- **Step operativi**: `10 / 17`
- **Stato attuale**: 🚀 In corso — Fase 3 (Sotto-Task 8.1 in avvio)

---

## 📋 Tabella di Tracciamento Dettagliata (Ordine Sinergico Bottom-Up)

| Fase | ID | Task / Sotto-Task | Difficoltà | Stato | Test (`pytest`) | Commit Hash | Data/Ora Completamento |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Init** | **Init** | Creazione e push branch `antigravity` | Bassa | ✅ Completato | — | `c04596d` | 2026-11-07 12:32 |
| **1. Fondamenta** | **Task 1** | Aggiornamento Schemi a Pydantic V2 e Standard Python 3.12+ | Bassa | ✅ Completato | 183 passed (0 warnings) | `e7e0c76` | 2026-11-07 17:35 |
| **1. Fondamenta** | **Task 2** | Correzioni di Stile PEP 8 e Annotazioni di Tipo (`Callable`, import) | Bassa | ✅ Completato | 183 passed (0 warnings) | `6f8524a` | 2026-11-07 17:39 |
| **1. Fondamenta** | **Task 3.1** | Evoluzione di `StructuredBrief` e introduzione del modello `PromptPackage` | Medio-Alta | ✅ Completato | 183 passed (0 warnings) | `4a45edf` | 2026-11-07 17:42 |
| **1. Fondamenta** | **Task 3.2** | Adeguamento Agenti, `StyleComplianceAgent` e `OutputManager` ai Modelli Tipizzati | Medio-Alta | ✅ Completato | 183 passed (0 warnings) | `5f42c40` | 2026-11-07 17:47 |
| **2. Rete & AI** | **Task 4** | Rotazione dei Log (`RotatingFileHandler`) e Gestione Cartella `logs/` | Bassa | ✅ Completato | 184 passed (0 warnings) | `6e7b9f5` | 2026-11-07 17:51 |
| **2. Rete & AI** | **Task 5** | Resilienza di Rete, Retry con Backoff (`tenacity`) e Timeout Configurabile | Media | ✅ Completato | 186 passed (0 warnings) | `43393a2` | 2026-11-07 17:58 |
| **2. Rete & AI** | **Task 6.1** | Definizione dei Protocolli Provider (`src/scenografia/providers/`) | Alta | ✅ Completato | 191 passed (0 warnings) | `d0bdca9` | 2026-11-07 18:02 |
| **2. Rete & AI** | **Task 6.2** | Creazione dei Subagent e della Skill Nativa Antigravity | Alta | ✅ Completato | 193 passed (0 warnings) | `3c17cd5` | 2026-11-07 18:03 |
| **3. Architettura** | **Task 7.1** | Creazione del package `src/scenografia/services/` ed estrazione delle Pipeline | Alta | ✅ Completato | 193 passed (0 warnings) | `5915c64` | 2026-11-07 18:06 |
| **3. Architettura** | **Task 7.2** | Aggiornamento di CLI e Web UI al nuovo Service Layer | Alta | ✅ Completato | 195 passed (0 warnings) | `52f7887` | 2026-11-07 18:09 |
| **3. Architettura** | **Task 8.1** | Estrazione dei Componenti UI in `src/scenografia/web/` | Alta | ⏳ Da fare | — | — | — |
| **3. Architettura** | **Task 8.2** | Implementazione della Galleria Storico (`history_gallery.py`) | Alta | ⏳ Da fare | — | — | — |
| **4. Feature** | **Task 9.1** | Sviluppo del modulo `SvgVectorizer` (`src/scenografia/tools/svg_vectorizer.py`) | Alta | ⏳ Da fare | — | — | — |
| **4. Feature** | **Task 9.2** | Integrazione dell'Export SVG in `OutputManager`, Service Layer, CLI e Web UI | Alta | ⏳ Da fare | — | — | — |
| **4. Feature** | **Task 10.1** | Estensione di `PromptEnhancerAgent` e `PromptTemplates` per i Piani di Profondità | Alta | ⏳ Da fare | — | — | — |
| **4. Feature** | **Task 10.2** | Integrazione del Selettore Piani di Profondità in Service Layer, CLI e Web UI | Alta | ⏳ Da fare | — | — | — |
| **5. CI/CD** | **Task 11** | Pipeline CI/CD (GitHub Actions) e Configurazione Linter/Type-Checker | Media | ⏳ Da fare | — | — | — |

---

## 📝 Checklist Rapida per Fasi

### Fase 1: Fondamenta Dati & Tipizzazione
- [x] **Init**: Creazione e configurazione branch `antigravity`
- [x] **Task 1**: Aggiornamento Schemi a Pydantic V2 e Standard Python 3.12+
- [x] **Task 2**: Correzioni di Stile PEP 8 e Annotazioni di Tipo
- [x] **Task 3**: Tipizzazione Rigida dei Contratti Dati tra Agenti
  - [x] **Sotto-Task 3.1**: Evoluzione di `StructuredBrief` e introduzione del modello `PromptPackage`
  - [x] **Sotto-Task 3.2**: Adeguamento Agenti, `StyleComplianceAgent` e `OutputManager` ai Modelli Tipizzati

### Fase 2: Infrastruttura, Rete & Provider AI (OpenRouter + Subagent Antigravity)
- [x] **Task 4**: Rotazione dei Log e Gestione Sicura della Cartella `logs/`
- [x] **Task 5**: Resilienza di Rete, Retry con Backoff e Timeout Configurabile
- [x] **Task 6**: Astrazione Provider AI e Trasformazione in Subagent di Antigravity
  - [x] **Sotto-Task 6.1**: Definizione dei Protocolli Provider (`src/scenografia/providers/`)
  - [x] **Sotto-Task 6.2**: Creazione dei Subagent e della Skill Nativa Antigravity

### Fase 3: Architettura Modulare (Service Layer & Web UI Componentizzata)
- [x] **Task 7**: Riorganizzazione Architetturale e Separazione del Service Layer
  - [x] **Sotto-Task 7.1**: Creazione del package `src/scenografia/services/` ed estrazione delle Pipeline
  - [x] **Sotto-Task 7.2**: Aggiornamento di CLI e Web UI al nuovo Service Layer
- [ ] **Task 8**: Modularizzazione della Web UI Streamlit e Galleria Storico
  - [ ] **Sotto-Task 8.1**: Estrazione dei Componenti UI in `src/scenografia/web/`
  - [ ] **Sotto-Task 8.2**: Implementazione della Galleria Storico (`history_gallery.py`)

### Fase 4: Nuove Funzionalità Scenografiche (Innestate sull'Architettura Pulita)
- [ ] **Task 9**: Vettorizzazione Effettiva (Export SVG Reale)
  - [ ] **Sotto-Task 9.1**: Sviluppo del modulo `SvgVectorizer`
  - [ ] **Sotto-Task 9.2**: Integrazione dell'Export SVG in `OutputManager`, Service Layer, CLI e Web UI
- [ ] **Task 10**: Layering Teatrale (Separazione Piani di Profondità Scenica)
  - [ ] **Sotto-Task 10.1**: Estensione di `PromptEnhancerAgent` e `PromptTemplates` per i Piani di Profondità
  - [ ] **Sotto-Task 10.2**: Integrazione del Selettore Piani di Profondità in Service Layer, CLI e Web UI

### Fase 5: Qualità del Codice e CI/CD Automation
- [ ] **Task 11**: Pipeline CI/CD con GitHub Actions e Configurazione Linter / Type-Checking
