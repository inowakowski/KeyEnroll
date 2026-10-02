"""Italian translations, keyed by the English source string."""

IT = {
    # -- navigation, header, session
    "Enroll": "Registrazione",
    "Credentials": "Credenziali",
    "Profiles": "Profili",
    "Instances": "Istanze",
    "(no instances configured)": "(nessuna istanza configurata)",
    "Signed in": "Accesso eseguito",
    "Not signed in": "Accesso non eseguito",
    "Sign in": "Accedi",
    "Sign out": "Disconnetti",
    "Complete the sign-in in your browser…": "Completare l’accesso nel browser…",
    "Sign-in failed": "Accesso non riuscito",
    "Not signed in. Sign in to the identity provider first.": (
        "Accesso non eseguito. Accedere prima al provider di identità."
    ),
    "The session has expired. Sign in to the identity provider again.": (
        "La sessione è scaduta. Accedere di nuovo al provider di identità."
    ),
    "Windows only lets administrators access FIDO security keys directly. Restart the "
    "application as administrator to detect and enroll keys.": (
        "Windows consente l’accesso diretto alle chiavi di sicurezza FIDO solo agli "
        "amministratori. Riavviare l’applicazione come amministratore per rilevare e "
        "registrare le chiavi."
    ),
    "Restart as administrator": "Riavvia come amministratore",
    "Enrollment in progress": "Registrazione in corso",
    "An enrollment is in progress. Cancel it and quit?": (
        "È in corso una registrazione. Annullarla e uscire?"
    ),
    # -- common
    "Error": "Errore",
    "Cancel": "Annulla",
    "Save": "Salva",
    "Delete": "Elimina",
    "Edit": "Modifica",
    "Close": "Chiudi",
    "Refresh": "Aggiorna",
    "Search": "Cerca",
    "Searching…": "Ricerca in corso…",
    "Name": "Nome",
    "Created": "Creazione",
    "Details": "Dettagli",
    "ID": "ID",
    "User": "Utente",
    "Username": "Nome utente",
    "Display name": "Nome visualizzato",
    "E-mail": "E-mail",
    "Name, username or e-mail": "Nome, nome utente o e-mail",
    "{count} user(s) found": "Utenti trovati: {count}",
    "No instance": "Nessuna istanza",
    "Add an identity provider instance first.": (
        "Aggiungere prima un’istanza di un provider di identità."
    ),
    "(none)": "(nessuno)",
    "(optional)": "(facoltativo)",
    # -- enroll page
    "1. User": "1. Utente",
    "2. Security key": "2. Chiave di sicurezza",
    "3. Enrollment options": "3. Opzioni di registrazione",
    "Profile": "Profilo",
    "Key display name": "Nome visualizzato della chiave",
    "e.g. YubiKey 5 NFC": "ad es. YubiKey 5 NFC",
    "Enroll security key": "Registra chiave",
    "No security key detected": "Nessuna chiave di sicurezza rilevata",
    "Insert a security key or place it on the NFC reader.": (
        "Inserire una chiave di sicurezza o appoggiarla sul lettore NFC."
    ),
    "PIN is set": "PIN impostato",
    "No PIN set": "Nessun PIN impostato",
    "minimum PIN length {length}": "lunghezza minima del PIN: {length}",
    "always UV enabled": "«richiedi sempre la verifica (UV)» attivo",
    "Enterprise Attestation enabled": "attestazione Enterprise attiva",
    "PIN change required": "modifica del PIN obbligatoria",
    "no support for advanced options": "opzioni avanzate non supportate",
    "Sign in to the identity provider first.": "Accedere prima al provider di identità.",
    "No user": "Nessun utente selezionato",
    "Search for a user and select one from the list.": (
        "Cercare un utente e selezionarlo nell’elenco."
    ),
    "No security key": "Nessuna chiave di sicurezza",
    "Confirm enrollment": "Conferma registrazione",
    "User: {user}": "Utente: {user}",
    "Security key: {key}": "Chiave di sicurezza: {key}",
    "The key will be factory reset. All FIDO credentials on it will be erased.": (
        "La chiave verrà riportata alle impostazioni di fabbrica. Tutte le credenziali "
        "FIDO presenti verranno cancellate."
    ),
    "Cancelling…": "Annullamento in corso…",
    "Enrollment failed": "Registrazione non riuscita",
    # -- profile options
    "Factory reset the security key": "Ripristina la chiave alle impostazioni di fabbrica",
    "Erases all FIDO credentials and the PIN on the key.": (
        "Cancella dalla chiave tutte le credenziali FIDO e il PIN."
    ),
    "Set new random PIN": "Imposta un nuovo PIN casuale",
    "Random PIN length": "Lunghezza del PIN casuale",
    "Minimum PIN length": "Lunghezza minima del PIN",
    "Force PIN change before use": "Imponi la modifica del PIN prima del primo utilizzo",
    "Require always UV": "Richiedi sempre la verifica dell’utente (UV)",
    "The key asks for the PIN on every use.": "La chiave chiede il PIN a ogni utilizzo.",
    "Require Enterprise Attestation": "Richiedi l’attestazione Enterprise",
    # -- profiles page
    "New profile": "Nuovo profilo",
    "Profile name": "Nome del profilo",
    "Profile settings": "Impostazioni del profilo",
    "Delete profile": "Elimina profilo",
    "Delete profile '{name}'?": "Eliminare il profilo «{name}»?",
    "A profile with this name already exists.": "Esiste già un profilo con questo nome.",
    "Profile name cannot be empty.": "Il nome del profilo non può essere vuoto.",
    "Minimum PIN length must be between 4 and 63.": (
        "La lunghezza minima del PIN deve essere compresa tra 4 e 63."
    ),
    "Random PIN length must be between 4 and 63.": (
        "La lunghezza del PIN casuale deve essere compresa tra 4 e 63."
    ),
    "Random PIN length cannot be shorter than the minimum PIN length.": (
        "Il PIN casuale non può essere più corto della lunghezza minima del PIN."
    ),
    # -- credentials page
    "FIDO credentials of the selected user": "Credenziali FIDO dell’utente selezionato",
    "Delete selected": "Elimina selezione",
    "Delete credential": "Elimina credenziale",
    "Delete credential '{name}' of {user}? The user will no longer be able to sign in "
    "with this key.": (
        "Eliminare la credenziale «{name}» di {user}? L’utente non potrà più accedere con "
        "questa chiave."
    ),
    "{provider} does not offer an API for listing or deleting credentials. Manage them "
    "in the provider's admin console.": (
        "{provider} non offre un’API per elencare o eliminare le credenziali. Gestirle "
        "nella console di amministrazione del provider."
    ),
    # -- instances page and dialog
    "Identity provider instances": "Istanze dei provider di identità",
    "Each instance is one tenant of an identity provider. Add as many as you need and "
    "switch between them with the selector at the top.": (
        "Ogni istanza corrisponde a un tenant di un provider di identità. Aggiungerne "
        "quante ne servono e passare dall’una all’altra con il selettore in alto."
    ),
    "Add instance": "Aggiungi istanza",
    "Edit instance": "Modifica istanza",
    "Set as active": "Imposta come attiva",
    "Delete instance": "Elimina istanza",
    "Delete instance '{name}' and its saved sign-in?": (
        "Eliminare l’istanza «{name}» e l’accesso salvato?"
    ),
    "Session": "Sessione",
    "Instance name": "Nome dell’istanza",
    "e.g. Production tenant": "ad es. Tenant di produzione",
    "Identity provider": "Provider di identità",
    "Default profile": "Profilo predefinito",
    "Use the values of the application registered for YubiEnroll at the identity "
    "provider. The redirect URI must match the registration exactly.": (
        "Usare i valori dell’applicazione registrata per YubiEnroll presso il provider di "
        "identità. L’URI di reindirizzamento deve corrispondere esattamente a quello "
        "della registrazione."
    ),
    "Instance name cannot be empty.": "Il nome dell’istanza non può essere vuoto.",
    "An instance with this name already exists.": "Esiste già un’istanza con questo nome.",
    "Required field is empty: {field}": "Campo obbligatorio vuoto: {field}",
    "The redirect URI must start with http://localhost.": (
        "L’URI di reindirizzamento deve iniziare con http://localhost."
    ),
    "Settings": "Impostazioni",
    "Language": "Lingua",
    # -- provider settings
    "Directory (tenant) ID": "ID della directory (tenant)",
    "Application (client) ID": "ID applicazione (client)",
    "Client ID": "ID client",
    "Redirect URI": "URI di reindirizzamento",
    "Entra ID endpoint": "Endpoint di Entra ID",
    "Microsoft Graph endpoint": "Endpoint di Microsoft Graph",
    "Change only for national cloud deployments.": (
        "Modificare solo per i cloud nazionali."
    ),
    "Okta domain": "Dominio Okta",
    "FIDO2 credentials are registered per domain (default or custom).": (
        "Le credenziali FIDO2 vengono registrate per dominio (predefinito o personalizzato)."
    ),
    "Environment ID": "Environment ID",
    "Region": "Regione",
    "Custom domain": "Dominio personalizzato",
    "MFA policy ID": "ID del criterio MFA",
    "Only if the environment uses a custom domain.": (
        "Solo se l’ambiente usa un dominio personalizzato."
    ),
    "Leave empty to use the default MFA policy.": (
        "Lasciare vuoto per usare il criterio MFA predefinito."
    ),
    "Tenant": "Tenant",
    "Realm": "Realm",
    "Journey name": "Nome del journey",
    "WebAuthn origin": "Origine WebAuthn",
    "The WebAuthn registration journey created for YubiEnroll.": (
        "Il journey di registrazione WebAuthn creato per YubiEnroll."
    ),
    "Leave empty to use the tenant address.": (
        "Lasciare vuoto per usare l’indirizzo del tenant."
    ),
    # -- PIN dialogs
    "Security key PIN": "PIN della chiave di sicurezza",
    "Enter the current PIN of the security key:": (
        "Immettere il PIN attuale della chiave di sicurezza:"
    ),
    "Wrong PIN.": "PIN errato.",
    "Attempts remaining: {retries}": "Tentativi rimasti: {retries}",
    "Show PIN": "Mostra PIN",
    "New PIN": "Nuovo PIN",
    "Repeat PIN": "Ripeti PIN",
    "Choose a PIN of at least {length} characters.": (
        "Scegliere un PIN di almeno {length} caratteri."
    ),
    "The PIN is too short.": "Il PIN è troppo corto.",
    "The PINs do not match.": "I PIN non corrispondono.",
    "The security key rejected this PIN (too short or too simple).": (
        "La chiave di sicurezza ha rifiutato questo PIN (troppo corto o troppo semplice)."
    ),
    # -- result dialog
    "Enrollment complete": "Registrazione completata",
    "The security key has been enrolled.": "La chiave di sicurezza è stata registrata.",
    "Serial number": "Numero di serie",
    "Temporary PIN:": "PIN temporaneo:",
    "The PIN you entered has been set on the key.": (
        "Il PIN immesso è stato impostato sulla chiave."
    ),
    "The PIN of the key was not changed.": "Il PIN della chiave non è stato modificato.",
    "The user must change the PIN before first use.": (
        "L’utente deve modificare il PIN prima del primo utilizzo."
    ),
    # -- enrollment engine: progress
    "Checking sign-in and permissions…": "Verifica dell’accesso e delle autorizzazioni…",
    "Factory reset: remove the security key now…": (
        "Ripristino: rimuovere ora la chiave di sicurezza…"
    ),
    "Factory reset: insert the security key again…": (
        "Ripristino: inserire di nuovo la chiave di sicurezza…"
    ),
    "Factory reset: touch the security key to confirm…": (
        "Ripristino: toccare la chiave di sicurezza per confermare…"
    ),
    "The security key has been reset.": "La chiave di sicurezza è stata ripristinata.",
    "Setting the PIN…": "Impostazione del PIN…",
    "Changing the PIN…": "Modifica del PIN…",
    "Setting the minimum PIN length to {length}…": (
        "Impostazione della lunghezza minima del PIN su {length}…"
    ),
    "Enabling 'Require always UV'…": "Attivazione di «richiedi sempre la verifica (UV)»…",
    "Enabling Enterprise Attestation…": "Attivazione dell’attestazione Enterprise…",
    "Requesting a registration challenge…": "Richiesta di una challenge di registrazione…",
    "Touch the security key to create the credential…": (
        "Toccare la chiave di sicurezza per creare la credenziale…"
    ),
    "Registering the credential with the identity provider…": (
        "Registrazione della credenziale presso il provider di identità…"
    ),
    "Forcing a PIN change before first use…": (
        "Attivazione della modifica obbligatoria del PIN prima del primo utilizzo…"
    ),
    "Done.": "Fatto.",
    # -- enrollment engine: errors
    "Enrollment cancelled.": "Registrazione annullata.",
    "No security key detected. Insert a key and try again.": (
        "Nessuna chiave di sicurezza rilevata. Inserire una chiave e riprovare."
    ),
    "The selected security key is no longer connected. Refresh the list.": (
        "La chiave di sicurezza selezionata non è più collegata. Aggiornare l’elenco."
    ),
    "Timed out waiting for the security key.": (
        "Tempo di attesa della chiave di sicurezza scaduto."
    ),
    "The key was not touched in time.": "La chiave non è stata toccata in tempo.",
    "This security key does not support FIDO2.": (
        "Questa chiave di sicurezza non supporta FIDO2."
    ),
    "This security key does not support a PIN.": (
        "Questa chiave di sicurezza non supporta il PIN."
    ),
    "This security key does not support 'Require always UV' (firmware 5.5+ needed).": (
        "Questa chiave di sicurezza non supporta «richiedi sempre la verifica (UV)» "
        "(è necessario il firmware 5.5 o successivo)."
    ),
    "This security key does not support Enterprise Attestation.": (
        "Questa chiave di sicurezza non supporta l’attestazione Enterprise."
    ),
    "This security key cannot enforce a minimum PIN length or a forced PIN change "
    "(firmware 5.5+ needed).": (
        "Questa chiave di sicurezza non può imporre una lunghezza minima del PIN né la "
        "modifica obbligatoria del PIN (è necessario il firmware 5.5 o successivo)."
    ),
    "The reset was not accepted. It must be confirmed within a few seconds of inserting "
    "the key.": (
        "Il ripristino non è stato accettato. Deve essere confermato entro pochi secondi "
        "dall’inserimento della chiave."
    ),
    "Factory reset failed.": "Ripristino delle impostazioni di fabbrica non riuscito.",
    "The current PIN is shorter than the minimum PIN length of the profile. Enable 'Set "
    "new random PIN' or 'Factory reset'.": (
        "Il PIN attuale è più corto della lunghezza minima del PIN prevista dal profilo. "
        "Attivare «Imposta un nuovo PIN casuale» o il ripristino delle impostazioni di "
        "fabbrica."
    ),
    "Too many wrong PIN attempts. Re-insert the key and try again.": (
        "Troppi tentativi di PIN errati. Reinserire la chiave e riprovare."
    ),
    "The PIN is blocked. The key must be factory reset.": (
        "Il PIN è bloccato. La chiave deve essere riportata alle impostazioni di fabbrica."
    ),
    "This security key is already registered for this user.": (
        "Questa chiave di sicurezza è già registrata per questo utente."
    ),
    "The identity provider returned an RP ID that does not match its origin.": (
        "Il provider di identità ha restituito un RP ID che non corrisponde alla sua origine."
    ),
    "The security key reported an error: {detail}": (
        "La chiave di sicurezza ha segnalato un errore: {detail}"
    ),
    "The credential was registered, but forcing a PIN change failed: {detail}": (
        "La credenziale è stata registrata, ma non è stato possibile attivare la modifica "
        "obbligatoria del PIN: {detail}"
    ),
    # -- bulk enrollment
    "Bulk enrollment": "Registrazione in blocco",
    "User list": "Elenco utenti",
    "Text or CSV file with one user per line: user name, login or e-mail. In a CSV with "
    "several columns, name the user column 'username'.": (
        "File di testo o CSV con un utente per riga: nome utente, login o e-mail. In un "
        "CSV con più colonne, chiamare «username» la colonna dell’utente."
    ),
    "Load from file…": "Carica da file…",
    "Load user list": "Carica elenco utenti",
    "User lists (*.csv *.txt);;All files (*)": (
        "Elenchi di utenti (*.csv *.txt);;Tutti i file (*)"
    ),
    "No users were found in this file.": "Nessun utente trovato in questo file.",
    "Clear list": "Svuota elenco",
    "Looking up users in the directory…": "Ricerca degli utenti nella directory…",
    "Load a user list to begin.": "Caricare un elenco di utenti per iniziare.",
    "Ready. Insert the first security key and press Start.": (
        "Pronto. Inserire la prima chiave di sicurezza e premere Avvia."
    ),
    "This list belongs to another instance. Export the results and clear it.": (
        "Questo elenco appartiene a un’altra istanza. Esportare i risultati e svuotarlo."
    ),
    "Enrollment options": "Opzioni di registrazione",
    "Add the serial number to the key name": (
        "Aggiungi il numero di serie al nome della chiave"
    ),
    "Show PINs in the list": "Mostra i PIN nell’elenco",
    "Start": "Avvia",
    "Stop": "Interrompi",
    "Retry failed": "Riprova non riusciti",
    "Export results…": "Esporta risultati…",
    "Export results": "Esporta risultati",
    "Export": "Esporta",
    "The file will contain the temporary PINs in plain text. Store it securely and delete "
    "it once the keys have been handed out.": (
        "Il file conterrà i PIN temporanei in chiaro. Conservarlo in modo sicuro ed "
        "eliminarlo dopo la consegna delle chiavi."
    ),
    "Results exported to {path}": "Risultati esportati in {path}",
    "Unsaved PINs": "PIN non salvati",
    "The temporary PINs have not been exported and will be lost. Continue?": (
        "I PIN temporanei non sono stati esportati e andranno persi. Continuare?"
    ),
    "Start bulk enrollment": "Avvia la registrazione in blocco",
    "{count} security key(s) will be enrolled, one per user.": (
        "Chiavi di sicurezza da registrare: {count} (una per utente)."
    ),
    "Every inserted key will be factory reset. All FIDO credentials on it will be erased.": (
        "Ogni chiave inserita verrà riportata alle impostazioni di fabbrica. Tutte le "
        "credenziali FIDO presenti verranno cancellate."
    ),
    "Bulk enrollment paused": "Registrazione in blocco in pausa",
    "{count} ready": "pronti: {count}",
    "{count} enrolled": "registrati: {count}",
    "{count} failed": "non riusciti: {count}",
    "{count} not found": "non trovati: {count}",
    "Checking…": "Verifica in corso…",
    "Ready": "Pronto",
    "Not found": "Non trovato",
    "In progress": "In corso",
    "Enrolled": "Registrato",
    "Failed": "Non riuscito",
    "Status": "Stato",
    "Key name": "Nome della chiave",
    "Temporary PIN": "PIN temporaneo",
    "Enrolled at": "Data di registrazione",
    "Message": "Messaggio",
    "Insert the security key for {user}…": "Inserire la chiave di sicurezza di {user}…",
    "Remove the previous key, then insert the key for {user}…": (
        "Rimuovere la chiave precedente, quindi inserire la chiave di {user}…"
    ),
    "Several security keys are connected. Leave only one connected.": (
        "Sono collegate più chiavi di sicurezza. Lasciarne collegata una sola."
    ),
    "Batch finished.": "Lotto completato.",
    "Security key {serial} was already enrolled in this batch.": (
        "La chiave di sicurezza {serial} è già stata registrata in questo lotto."
    ),
    # -- key details and naming
    "Firmware": "Firmware",
    "Ready to enroll.": "Pronta per la registrazione.",
    "serial number not readable": "numero di serie non leggibile",
    "Key will be registered as: {name}": "La chiave verrà registrata come: {name}",
    "Key name: {name}": "Nome della chiave: {name}",
    # -- profile summary
    "factory reset": "ripristino di fabbrica",
    "no factory reset": "nessun ripristino di fabbrica",
    "random PIN of {length} digits": "PIN casuale di {length} cifre",
    "PIN entered by the operator": "PIN immesso dall’operatore",
    "forced PIN change": "modifica del PIN obbligatoria",
    "always UV": "richiedi sempre la verifica (UV)",
    "Enterprise Attestation": "attestazione Enterprise",
    # -- appearance
    "Appearance": "Aspetto",
    "Light": "Chiaro",
    "Dark": "Scuro",
    "Custom": "Personalizzato",
    "Custom colours": "Colori personalizzati",
    "Accent colour…": "Colore principale…",
    "Choose the accent colour": "Scegli il colore principale",
    "Restart the application to apply the change.": (
        "Riavviare l’applicazione per applicare la modifica."
    ),
    "Version {version}": "Versione {version}",
    # -- hand-over to the user
    "Pass it on to the user": "Consegna all’utente",
    "The message contains the PIN. Send it through a different channel than the key "
    "itself.": (
        "Il messaggio contiene il PIN. Inviarlo tramite un canale diverso da quello "
        "usato per la chiave."
    ),
    "Copy PIN": "Copia PIN",
    "Copy message": "Copia messaggio",
    "E-mail draft…": "Bozza di e-mail…",
    "Save to file…": "Salva su file…",
    "Save message": "Salva messaggio",
    "Text files (*.txt)": "File di testo (*.txt)",
    "Copied. The clipboard will be cleared in one minute.": (
        "Copiato. Gli appunti verranno svuotati tra un minuto."
    ),
    "Saved to {path}. The file contains the PIN.": (
        "Salvato in {path}. Il file contiene il PIN."
    ),
    "The PIN is not stored anywhere. It is shown only in this window.": (
        "Il PIN non viene salvato da nessuna parte. È visibile solo in questa finestra."
    ),
    "No e-mail address is known for this user.": (
        "Non è noto alcun indirizzo e-mail per questo utente."
    ),
    "A draft was opened in your e-mail program. Review it and send it.": (
        "È stata aperta una bozza nel programma di posta. Controllarla e inviarla."
    ),
    "No e-mail program is available. Copy the message instead.": (
        "Nessun programma di posta disponibile. Copiare il messaggio."
    ),
    "security key": "chiave di sicurezza",
    "(provided separately)": "(comunicato separatamente)",
    "You will be asked to set your own PIN the first time you use the key.": (
        "Al primo utilizzo della chiave verrà chiesto di impostare un PIN personale."
    ),
    "Message for the user…": "Messaggio per l’utente…",
    "Select an enrolled user to copy, e-mail or save the hand-over message.": (
        "Selezionare un utente registrato per copiare, inviare per e-mail o salvare il "
        "messaggio di consegna."
    ),
    # -- export options
    "CSV files (*.csv)": "File CSV (*.csv)",
    "Enrolled users only": "Solo utenti registrati",
    "All users on the list, with their status": (
        "Tutti gli utenti dell’elenco, con il relativo stato"
    ),
    "Include temporary PINs": "Includi i PIN temporanei",
    "CSV, semicolon separated": "CSV separato da punto e virgola",
    "CSV, comma separated": "CSV separato da virgole",
    "Format": "Formato",
    # -- settings page
    "Colour scheme": "Combinazione di colori",
    "Same as the system (light or dark)": "Come il sistema (chiaro o scuro)",
    "Same as the system": "Come il sistema",
    "Message for the user": "Messaggio per l’utente",
    "Used after an enrollment for the e-mail draft, the copied message and the saved "
    "file. Placeholders: {placeholders}.": (
        "Usato dopo una registrazione per la bozza di e-mail, il messaggio copiato e il "
        "file salvato. Segnaposto: {placeholders}."
    ),
    "Subject": "Oggetto",
    "Text": "Testo",
    "Restore the default text": "Ripristina il testo predefinito",
    "Saved.": "Salvato.",
    "The default text has been restored.": "Il testo predefinito è stato ripristinato.",
    "About": "Informazioni",
    "Version": "Versione",
    "License": "Licenza",
    "Project page": "Pagina del progetto",
    "Documentation": "Documentazione",
    "KeyEnroll is an independent open-source project. It is not affiliated with or "
    "endorsed by Yubico, Microsoft, Okta or Ping Identity.": (
        "KeyEnroll è un progetto open source indipendente. Non è affiliato a Yubico, "
        "Microsoft, Okta o Ping Identity, né è da essi approvato."
    ),
    "Open the folder with settings and logs": "Apri la cartella con impostazioni e log",
    # -- unexpected errors
    "An unexpected error occurred:": "Si è verificato un errore imprevisto:",
    "Details were written to the log: {path}": "I dettagli sono stati scritti nel log: {path}",
    "The settings file could not be read and was set aside as {path}. KeyEnroll started "
    "with default settings.": (
        "Non è stato possibile leggere il file delle impostazioni, che è stato messo da "
        "parte come {path}. KeyEnroll è stato avviato con le impostazioni predefinite."
    ),
    # -- updates
    "Check for updates": "Verifica aggiornamenti",
    "Checking for updates…": "Verifica degli aggiornamenti…",
    "Open the download page": "Apri la pagina di download",
    "Version {latest} is available (you have {current}).": (
        "È disponibile la versione {latest} (versione installata: {current})."
    ),
    "You have the latest version ({current}).": (
        "È installata la versione più recente ({current})."
    ),
    "Could not reach the update server. Check the connection.": (
        "Impossibile raggiungere il server degli aggiornamenti. Controllare la connessione."
    ),
    "No published release was found.": "Nessuna versione pubblicata trovata.",
    "The update server is busy. Try again in a few minutes.": (
        "Il server degli aggiornamenti è occupato. Riprovare tra qualche minuto."
    ),
    "The update server returned an unexpected answer.": (
        "Il server degli aggiornamenti ha restituito una risposta imprevista."
    ),
}
