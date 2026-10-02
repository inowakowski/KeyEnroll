"""French translations, keyed by the English source string."""

FR = {
    # -- navigation, header, session
    "Enroll": "Enregistrement",
    "Credentials": "Identifiants",
    "Profiles": "Profils",
    "Instances": "Instances",
    "(no instances configured)": "(aucune instance configurée)",
    "Signed in": "Connecté",
    "Not signed in": "Non connecté",
    "Sign in": "Se connecter",
    "Sign out": "Se déconnecter",
    "Complete the sign-in in your browser…": "Terminez la connexion dans votre navigateur…",
    "Sign-in failed": "Échec de la connexion",
    "Not signed in. Sign in to the identity provider first.": (
        "Non connecté. Connectez-vous d’abord au fournisseur d’identité."
    ),
    "The session has expired. Sign in to the identity provider again.": (
        "La session a expiré. Reconnectez-vous au fournisseur d’identité."
    ),
    "Windows only lets administrators access FIDO security keys directly. Restart the "
    "application as administrator to detect and enroll keys.": (
        "Windows n’autorise l’accès direct aux clés de sécurité FIDO qu’aux "
        "administrateurs. Redémarrez l’application en tant qu’administrateur pour "
        "détecter et enregistrer des clés."
    ),
    "Restart as administrator": "Redémarrer en tant qu’administrateur",
    "Enrollment in progress": "Enregistrement en cours",
    "An enrollment is in progress. Cancel it and quit?": (
        "Un enregistrement est en cours. L’annuler et quitter\u00a0?"
    ),
    # -- common
    "Error": "Erreur",
    "Cancel": "Annuler",
    "Save": "Enregistrer",
    "Delete": "Supprimer",
    "Edit": "Modifier",
    "Close": "Fermer",
    "Refresh": "Actualiser",
    "Search": "Rechercher",
    "Searching…": "Recherche…",
    "Name": "Nom",
    "Created": "Création",
    "Details": "Détails",
    "ID": "ID",
    "User": "Utilisateur",
    "Username": "Nom d’utilisateur",
    "Display name": "Nom d’affichage",
    "E-mail": "E-mail",
    "Name, username or e-mail": "Nom, nom d’utilisateur ou e-mail",
    "{count} user(s) found": "Utilisateurs trouvés\u00a0: {count}",
    "No instance": "Aucune instance",
    "Add an identity provider instance first.": (
        "Ajoutez d’abord une instance de fournisseur d’identité."
    ),
    "(none)": "(aucun)",
    "(optional)": "(facultatif)",
    # -- enroll page
    "1. User": "1. Utilisateur",
    "2. Security key": "2. Clé de sécurité",
    "3. Enrollment options": "3. Options d’enregistrement",
    "Profile": "Profil",
    "Key display name": "Nom affiché de la clé",
    "e.g. YubiKey 5 NFC": "p. ex. YubiKey 5 NFC",
    "Enroll security key": "Enregistrer la clé",
    "No security key detected": "Aucune clé de sécurité détectée",
    "Insert a security key or place it on the NFC reader.": (
        "Insérez une clé de sécurité ou posez-la sur le lecteur NFC."
    ),
    "PIN is set": "Code PIN défini",
    "No PIN set": "Aucun code PIN",
    "minimum PIN length {length}": "longueur minimale du code PIN\u00a0: {length}",
    "always UV enabled": "«\u00a0toujours exiger la vérification (UV)\u00a0» activé",
    "Enterprise Attestation enabled": "attestation Enterprise activée",
    "PIN change required": "changement de code PIN requis",
    "no support for advanced options": "options avancées non prises en charge",
    "Sign in to the identity provider first.": (
        "Connectez-vous d’abord au fournisseur d’identité."
    ),
    "No user": "Aucun utilisateur sélectionné",
    "Search for a user and select one from the list.": (
        "Recherchez un utilisateur et sélectionnez-le dans la liste."
    ),
    "No security key": "Aucune clé de sécurité",
    "Confirm enrollment": "Confirmer l’enregistrement",
    "User: {user}": "Utilisateur\u00a0: {user}",
    "Security key: {key}": "Clé de sécurité\u00a0: {key}",
    "The key will be factory reset. All FIDO credentials on it will be erased.": (
        "La clé sera réinitialisée aux paramètres d’usine. Tous les identifiants FIDO "
        "qu’elle contient seront effacés."
    ),
    "Cancelling…": "Annulation…",
    "Enrollment failed": "Échec de l’enregistrement",
    # -- profile options
    "Factory reset the security key": "Réinitialiser la clé aux paramètres d’usine",
    "Erases all FIDO credentials and the PIN on the key.": (
        "Efface de la clé tous les identifiants FIDO ainsi que le code PIN."
    ),
    "Set new random PIN": "Définir un nouveau code PIN aléatoire",
    "Random PIN length": "Longueur du code PIN aléatoire",
    "Minimum PIN length": "Longueur minimale du code PIN",
    "Force PIN change before use": "Imposer le changement du code PIN avant la première utilisation",
    "Require always UV": "Toujours exiger la vérification de l’utilisateur (UV)",
    "The key asks for the PIN on every use.": (
        "La clé demande le code PIN à chaque utilisation."
    ),
    "Require Enterprise Attestation": "Exiger l’attestation Enterprise",
    # -- profiles page
    "New profile": "Nouveau profil",
    "Profile name": "Nom du profil",
    "Profile settings": "Paramètres du profil",
    "Delete profile": "Supprimer le profil",
    "Delete profile '{name}'?": "Supprimer le profil «\u00a0{name}\u00a0»\u00a0?",
    "A profile with this name already exists.": "Un profil portant ce nom existe déjà.",
    "Profile name cannot be empty.": "Le nom du profil ne peut pas être vide.",
    "Minimum PIN length must be between 4 and 63.": (
        "La longueur minimale du code PIN doit être comprise entre 4 et 63."
    ),
    "Random PIN length must be between 4 and 63.": (
        "La longueur du code PIN aléatoire doit être comprise entre 4 et 63."
    ),
    "Random PIN length cannot be shorter than the minimum PIN length.": (
        "Le code PIN aléatoire ne peut pas être plus court que la longueur minimale du "
        "code PIN."
    ),
    # -- credentials page
    "FIDO credentials of the selected user": (
        "Identifiants FIDO de l’utilisateur sélectionné"
    ),
    "Delete selected": "Supprimer la sélection",
    "Delete credential": "Supprimer l’identifiant",
    "Delete credential '{name}' of {user}? The user will no longer be able to sign in "
    "with this key.": (
        "Supprimer l’identifiant «\u00a0{name}\u00a0» de {user}\u00a0? L’utilisateur ne pourra plus se "
        "connecter avec cette clé."
    ),
    "{provider} does not offer an API for listing or deleting credentials. Manage them "
    "in the provider's admin console.": (
        "{provider} ne propose pas d’API pour lister ou supprimer les identifiants. "
        "Gérez-les dans la console d’administration du fournisseur."
    ),
    # -- instances page and dialog
    "Identity provider instances": "Instances de fournisseurs d’identité",
    "Each instance is one tenant of an identity provider. Add as many as you need and "
    "switch between them with the selector at the top.": (
        "Chaque instance correspond à un tenant d’un fournisseur d’identité. Ajoutez-en "
        "autant que nécessaire et passez de l’une à l’autre avec la liste en haut de la "
        "fenêtre."
    ),
    "Add instance": "Ajouter une instance",
    "Edit instance": "Modifier l’instance",
    "Set as active": "Définir comme active",
    "Delete instance": "Supprimer l’instance",
    "Delete instance '{name}' and its saved sign-in?": (
        "Supprimer l’instance «\u00a0{name}\u00a0» et sa connexion enregistrée\u00a0?"
    ),
    "Session": "Session",
    "Instance name": "Nom de l’instance",
    "e.g. Production tenant": "p. ex. Tenant de production",
    "Identity provider": "Fournisseur d’identité",
    "Default profile": "Profil par défaut",
    "Use the values of the application registered for YubiEnroll at the identity "
    "provider. The redirect URI must match the registration exactly.": (
        "Utilisez les valeurs de l’application enregistrée pour YubiEnroll auprès du "
        "fournisseur d’identité. L’URI de redirection doit correspondre exactement à "
        "celle de l’enregistrement."
    ),
    "Instance name cannot be empty.": "Le nom de l’instance ne peut pas être vide.",
    "An instance with this name already exists.": (
        "Une instance portant ce nom existe déjà."
    ),
    "Required field is empty: {field}": "Champ obligatoire vide\u00a0: {field}",
    "The redirect URI must start with http://localhost.": (
        "L’URI de redirection doit commencer par http://localhost."
    ),
    "Settings": "Paramètres",
    "Language": "Langue",
    # -- provider settings
    "Directory (tenant) ID": "ID de l’annuaire (locataire)",
    "Application (client) ID": "ID d’application (client)",
    "Client ID": "ID client",
    "Redirect URI": "URI de redirection",
    "Entra ID endpoint": "Point de terminaison Entra ID",
    "Microsoft Graph endpoint": "Point de terminaison Microsoft Graph",
    "Change only for national cloud deployments.": (
        "À modifier uniquement pour les clouds nationaux."
    ),
    "Okta domain": "Domaine Okta",
    "FIDO2 credentials are registered per domain (default or custom).": (
        "Les identifiants FIDO2 sont enregistrés par domaine (par défaut ou personnalisé)."
    ),
    "Environment ID": "Environment ID",
    "Region": "Région",
    "Custom domain": "Domaine personnalisé",
    "MFA policy ID": "ID de la stratégie MFA",
    "Only if the environment uses a custom domain.": (
        "Uniquement si l’environnement utilise un domaine personnalisé."
    ),
    "Leave empty to use the default MFA policy.": (
        "Laissez vide pour utiliser la stratégie MFA par défaut."
    ),
    "Tenant": "Tenant",
    "Realm": "Realm",
    "Journey name": "Nom de la journey",
    "WebAuthn origin": "Origine WebAuthn",
    "The WebAuthn registration journey created for YubiEnroll.": (
        "La journey d’enregistrement WebAuthn créée pour YubiEnroll."
    ),
    "Leave empty to use the tenant address.": (
        "Laissez vide pour utiliser l’adresse du tenant."
    ),
    # -- PIN dialogs
    "Security key PIN": "Code PIN de la clé de sécurité",
    "Enter the current PIN of the security key:": (
        "Saisissez le code PIN actuel de la clé de sécurité\u00a0:"
    ),
    "Wrong PIN.": "Code PIN incorrect.",
    "Attempts remaining: {retries}": "Tentatives restantes\u00a0: {retries}",
    "Show PIN": "Afficher le code PIN",
    "New PIN": "Nouveau code PIN",
    "Repeat PIN": "Répéter le code PIN",
    "Choose a PIN of at least {length} characters.": (
        "Choisissez un code PIN d’au moins {length} caractères."
    ),
    "The PIN is too short.": "Le code PIN est trop court.",
    "The PINs do not match.": "Les codes PIN ne correspondent pas.",
    "The security key rejected this PIN (too short or too simple).": (
        "La clé de sécurité a refusé ce code PIN (trop court ou trop simple)."
    ),
    # -- result dialog
    "Enrollment complete": "Enregistrement terminé",
    "The security key has been enrolled.": "La clé de sécurité a été enregistrée.",
    "Serial number": "Numéro de série",
    "Temporary PIN:": "Code PIN temporaire\u00a0:",
    "The PIN you entered has been set on the key.": (
        "Le code PIN que vous avez saisi a été défini sur la clé."
    ),
    "The PIN of the key was not changed.": "Le code PIN de la clé n’a pas été modifié.",
    "The user must change the PIN before first use.": (
        "L’utilisateur doit changer le code PIN avant la première utilisation."
    ),
    # -- enrollment engine: progress
    "Checking sign-in and permissions…": "Vérification de la connexion et des autorisations…",
    "Factory reset: remove the security key now…": (
        "Réinitialisation\u00a0: retirez maintenant la clé de sécurité…"
    ),
    "Factory reset: insert the security key again…": (
        "Réinitialisation\u00a0: insérez de nouveau la clé de sécurité…"
    ),
    "Factory reset: touch the security key to confirm…": (
        "Réinitialisation\u00a0: touchez la clé de sécurité pour confirmer…"
    ),
    "The security key has been reset.": "La clé de sécurité a été réinitialisée.",
    "Setting the PIN…": "Définition du code PIN…",
    "Changing the PIN…": "Modification du code PIN…",
    "Setting the minimum PIN length to {length}…": (
        "Réglage de la longueur minimale du code PIN sur {length}…"
    ),
    "Enabling 'Require always UV'…": "Activation de «\u00a0toujours exiger la vérification (UV)\u00a0»…",
    "Enabling Enterprise Attestation…": "Activation de l’attestation Enterprise…",
    "Requesting a registration challenge…": "Demande d’un défi d’enregistrement…",
    "Touch the security key to create the credential…": (
        "Touchez la clé de sécurité pour créer l’identifiant…"
    ),
    "Registering the credential with the identity provider…": (
        "Enregistrement de l’identifiant auprès du fournisseur d’identité…"
    ),
    "Forcing a PIN change before first use…": (
        "Activation du changement obligatoire du code PIN avant la première utilisation…"
    ),
    "Done.": "Terminé.",
    # -- enrollment engine: errors
    "Enrollment cancelled.": "Enregistrement annulé.",
    "No security key detected. Insert a key and try again.": (
        "Aucune clé de sécurité détectée. Insérez une clé et réessayez."
    ),
    "The selected security key is no longer connected. Refresh the list.": (
        "La clé de sécurité sélectionnée n’est plus connectée. Actualisez la liste."
    ),
    "Timed out waiting for the security key.": (
        "Délai d’attente de la clé de sécurité dépassé."
    ),
    "The key was not touched in time.": "La clé n’a pas été touchée à temps.",
    "This security key does not support FIDO2.": (
        "Cette clé de sécurité ne prend pas en charge FIDO2."
    ),
    "This security key does not support a PIN.": (
        "Cette clé de sécurité ne prend pas en charge le code PIN."
    ),
    "This security key does not support 'Require always UV' (firmware 5.5+ needed).": (
        "Cette clé de sécurité ne prend pas en charge «\u00a0toujours exiger la vérification "
        "(UV)\u00a0» (firmware 5.5 ou ultérieur requis)."
    ),
    "This security key does not support Enterprise Attestation.": (
        "Cette clé de sécurité ne prend pas en charge l’attestation Enterprise."
    ),
    "This security key cannot enforce a minimum PIN length or a forced PIN change "
    "(firmware 5.5+ needed).": (
        "Cette clé de sécurité ne peut imposer ni une longueur minimale du code PIN ni "
        "un changement de code PIN (firmware 5.5 ou ultérieur requis)."
    ),
    "The reset was not accepted. It must be confirmed within a few seconds of inserting "
    "the key.": (
        "La réinitialisation n’a pas été acceptée. Elle doit être confirmée dans les "
        "quelques secondes qui suivent l’insertion de la clé."
    ),
    "Factory reset failed.": "Échec de la réinitialisation aux paramètres d’usine.",
    "The current PIN is shorter than the minimum PIN length of the profile. Enable 'Set "
    "new random PIN' or 'Factory reset'.": (
        "Le code PIN actuel est plus court que la longueur minimale définie dans le "
        "profil. Activez «\u00a0Définir un nouveau code PIN aléatoire\u00a0» ou la réinitialisation "
        "aux paramètres d’usine."
    ),
    "Too many wrong PIN attempts. Re-insert the key and try again.": (
        "Trop de codes PIN incorrects. Réinsérez la clé et réessayez."
    ),
    "The PIN is blocked. The key must be factory reset.": (
        "Le code PIN est bloqué. La clé doit être réinitialisée aux paramètres d’usine."
    ),
    "This security key is already registered for this user.": (
        "Cette clé de sécurité est déjà enregistrée pour cet utilisateur."
    ),
    "The identity provider returned an RP ID that does not match its origin.": (
        "Le fournisseur d’identité a renvoyé un RP ID qui ne correspond pas à son origine."
    ),
    "The security key reported an error: {detail}": (
        "La clé de sécurité a signalé une erreur\u00a0: {detail}"
    ),
    "The credential was registered, but forcing a PIN change failed: {detail}": (
        "L’identifiant a été enregistré, mais le changement obligatoire du code PIN n’a "
        "pas pu être activé\u00a0: {detail}"
    ),
    # -- bulk enrollment
    "Bulk enrollment": "Enregistrement en masse",
    "User list": "Liste des utilisateurs",
    "Text or CSV file with one user per line: user name, login or e-mail. In a CSV with "
    "several columns, name the user column 'username'.": (
        "Fichier texte ou CSV avec un utilisateur par ligne\u00a0: nom d’utilisateur, "
        "identifiant de connexion ou e-mail. Dans un CSV à plusieurs colonnes, nommez la "
        "colonne des utilisateurs «\u00a0username\u00a0»."
    ),
    "Load from file…": "Charger depuis un fichier…",
    "Load user list": "Charger la liste des utilisateurs",
    "User lists (*.csv *.txt);;All files (*)": (
        "Listes d’utilisateurs (*.csv *.txt);;Tous les fichiers (*)"
    ),
    "No users were found in this file.": "Aucun utilisateur trouvé dans ce fichier.",
    "Clear list": "Vider la liste",
    "Looking up users in the directory…": "Recherche des utilisateurs dans l’annuaire…",
    "Load a user list to begin.": "Chargez une liste d’utilisateurs pour commencer.",
    "Ready. Insert the first security key and press Start.": (
        "Prêt. Insérez la première clé de sécurité et cliquez sur Démarrer."
    ),
    "This list belongs to another instance. Export the results and clear it.": (
        "Cette liste appartient à une autre instance. Exportez les résultats et videz-la."
    ),
    "Enrollment options": "Options d’enregistrement",
    "Add the serial number to the key name": "Ajouter le numéro de série au nom de la clé",
    "Show PINs in the list": "Afficher les codes PIN dans la liste",
    "Start": "Démarrer",
    "Stop": "Arrêter",
    "Retry failed": "Réessayer les échecs",
    "Export results…": "Exporter les résultats…",
    "Export results": "Exporter les résultats",
    "Export": "Exporter",
    "The file will contain the temporary PINs in plain text. Store it securely and delete "
    "it once the keys have been handed out.": (
        "Le fichier contiendra les codes PIN temporaires en clair. Conservez-le en lieu "
        "sûr et supprimez-le une fois les clés remises."
    ),
    "Results exported to {path}": "Résultats exportés vers {path}",
    "Unsaved PINs": "Codes PIN non enregistrés",
    "The temporary PINs have not been exported and will be lost. Continue?": (
        "Les codes PIN temporaires n’ont pas été exportés et seront perdus. Continuer\u00a0?"
    ),
    "Start bulk enrollment": "Démarrer l’enregistrement en masse",
    "{count} security key(s) will be enrolled, one per user.": (
        "Clés de sécurité à enregistrer\u00a0: {count} (une par utilisateur)."
    ),
    "Every inserted key will be factory reset. All FIDO credentials on it will be erased.": (
        "Chaque clé insérée sera réinitialisée aux paramètres d’usine. Tous les "
        "identifiants FIDO qu’elle contient seront effacés."
    ),
    "Bulk enrollment paused": "Enregistrement en masse suspendu",
    "{count} ready": "prêts\u00a0: {count}",
    "{count} enrolled": "enregistrés\u00a0: {count}",
    "{count} failed": "en échec\u00a0: {count}",
    "{count} not found": "introuvables\u00a0: {count}",
    "Checking…": "Vérification…",
    "Ready": "Prêt",
    "Not found": "Introuvable",
    "In progress": "En cours",
    "Enrolled": "Enregistré",
    "Failed": "Échec",
    "Status": "État",
    "Key name": "Nom de la clé",
    "Temporary PIN": "Code PIN temporaire",
    "Enrolled at": "Date d’enregistrement",
    "Message": "Message",
    "Insert the security key for {user}…": "Insérez la clé de sécurité de {user}…",
    "Remove the previous key, then insert the key for {user}…": (
        "Retirez la clé précédente, puis insérez la clé de {user}…"
    ),
    "Several security keys are connected. Leave only one connected.": (
        "Plusieurs clés de sécurité sont connectées. N’en laissez qu’une seule."
    ),
    "Batch finished.": "Lot terminé.",
    "Security key {serial} was already enrolled in this batch.": (
        "La clé de sécurité {serial} a déjà été enregistrée dans ce lot."
    ),
    # -- key details and naming
    "Firmware": "Firmware",
    "Ready to enroll.": "Prête à être enregistrée.",
    "serial number not readable": "numéro de série illisible",
    "Key will be registered as: {name}": "La clé sera enregistrée sous le nom\u00a0: {name}",
    "Key name: {name}": "Nom de la clé\u00a0: {name}",
    # -- profile summary
    "factory reset": "réinitialisation d’usine",
    "no factory reset": "sans réinitialisation d’usine",
    "random PIN of {length} digits": "code PIN aléatoire de {length} chiffres",
    "PIN entered by the operator": "code PIN saisi par l’opérateur",
    "forced PIN change": "changement de code PIN imposé",
    "always UV": "toujours exiger la vérification (UV)",
    "Enterprise Attestation": "attestation Enterprise",
    # -- appearance
    "Appearance": "Apparence",
    "Light": "Clair",
    "Dark": "Sombre",
    "Custom": "Personnalisé",
    "Custom colours": "Couleurs personnalisées",
    "Accent colour…": "Couleur d’accentuation…",
    "Choose the accent colour": "Choisir la couleur d’accentuation",
    "Restart the application to apply the change.": (
        "Redémarrez l’application pour appliquer la modification."
    ),
    "Version {version}": "Version {version}",
    # -- hand-over to the user
    "Pass it on to the user": "Transmettre à l’utilisateur",
    "The message contains the PIN. Send it through a different channel than the key "
    "itself.": (
        "Le message contient le code PIN. Envoyez-le par un autre canal que la clé "
        "elle-même."
    ),
    "Copy PIN": "Copier le code PIN",
    "Copy message": "Copier le message",
    "E-mail draft…": "Brouillon d’e-mail…",
    "Save to file…": "Enregistrer dans un fichier…",
    "Save message": "Enregistrer le message",
    "Text files (*.txt)": "Fichiers texte (*.txt)",
    "Copied. The clipboard will be cleared in one minute.": (
        "Copié. Le presse-papiers sera vidé dans une minute."
    ),
    "Saved to {path}. The file contains the PIN.": (
        "Enregistré dans {path}. Le fichier contient le code PIN."
    ),
    "The PIN is not stored anywhere. It is shown only in this window.": (
        "Le code PIN n’est stocké nulle part. Il n’est affiché que dans cette fenêtre."
    ),
    "No e-mail address is known for this user.": (
        "Aucune adresse e-mail n’est connue pour cet utilisateur."
    ),
    "A draft was opened in your e-mail program. Review it and send it.": (
        "Un brouillon a été ouvert dans votre logiciel de messagerie. Vérifiez-le et "
        "envoyez-le."
    ),
    "No e-mail program is available. Copy the message instead.": (
        "Aucun logiciel de messagerie n’est disponible. Copiez plutôt le message."
    ),
    "security key": "clé de sécurité",
    "(provided separately)": "(communiqué séparément)",
    "You will be asked to set your own PIN the first time you use the key.": (
        "Lors de la première utilisation de la clé, vous devrez définir votre propre "
        "code PIN."
    ),
    "Message for the user…": "Message pour l’utilisateur…",
    "Select an enrolled user to copy, e-mail or save the hand-over message.": (
        "Sélectionnez un utilisateur enregistré pour copier, envoyer par e-mail ou "
        "enregistrer le message de remise."
    ),
    # -- export options
    "CSV files (*.csv)": "Fichiers CSV (*.csv)",
    "Enrolled users only": "Utilisateurs enregistrés uniquement",
    "All users on the list, with their status": (
        "Tous les utilisateurs de la liste, avec leur état"
    ),
    "Include temporary PINs": "Inclure les codes PIN temporaires",
    "CSV, semicolon separated": "CSV, séparé par des points-virgules",
    "CSV, comma separated": "CSV, séparé par des virgules",
    "Format": "Format",
    # -- settings page
    "Colour scheme": "Jeu de couleurs",
    "Same as the system (light or dark)": "Identique au système (clair ou sombre)",
    "Same as the system": "Identique au système",
    "Message for the user": "Message pour l’utilisateur",
    "Used after an enrollment for the e-mail draft, the copied message and the saved "
    "file. Placeholders: {placeholders}.": (
        "Utilisé après un enregistrement pour le brouillon d’e-mail, le message copié et "
        "le fichier enregistré. Champs disponibles\u00a0: {placeholders}."
    ),
    "Subject": "Objet",
    "Text": "Texte",
    "Restore the default text": "Rétablir le texte par défaut",
    "Saved.": "Enregistré.",
    "The default text has been restored.": "Le texte par défaut a été rétabli.",
    "About": "À propos",
    "Version": "Version",
    "License": "Licence",
    "Project page": "Page du projet",
    "Documentation": "Documentation",
    "KeyEnroll is an independent open-source project. It is not affiliated with or "
    "endorsed by Yubico, Microsoft, Okta or Ping Identity.": (
        "KeyEnroll est un projet open source indépendant. Il n’est ni affilié à Yubico, "
        "Microsoft, Okta ou Ping Identity, ni approuvé par ces sociétés."
    ),
    "Open the folder with settings and logs": "Ouvrir le dossier des paramètres et des journaux",
    # -- unexpected errors
    "An unexpected error occurred:": "Une erreur inattendue s’est produite\u00a0:",
    "Details were written to the log: {path}": (
        "Les détails ont été consignés dans le journal\u00a0: {path}"
    ),
    "The settings file could not be read and was set aside as {path}. KeyEnroll started "
    "with default settings.": (
        "Le fichier de paramètres n’a pas pu être lu et a été mis de côté sous le nom "
        "{path}. KeyEnroll a démarré avec les paramètres par défaut."
    ),
    # -- updates
    "Check for updates": "Rechercher des mises à jour",
    "Checking for updates…": "Recherche de mises à jour…",
    "Open the download page": "Ouvrir la page de téléchargement",
    "Version {latest} is available (you have {current}).": (
        "La version {latest} est disponible (vous avez la {current})."
    ),
    "You have the latest version ({current}).": (
        "Vous disposez de la dernière version ({current})."
    ),
    "Could not reach the update server. Check the connection.": (
        "Impossible de joindre le serveur de mises à jour. Vérifiez la connexion."
    ),
    "No published release was found.": "Aucune version publiée n’a été trouvée.",
    "The update server is busy. Try again in a few minutes.": (
        "Le serveur de mises à jour est occupé. Réessayez dans quelques minutes."
    ),
    "The update server returned an unexpected answer.": (
        "Le serveur de mises à jour a renvoyé une réponse inattendue."
    ),
}
