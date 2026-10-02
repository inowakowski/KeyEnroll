"""Spanish translations, keyed by the English source string."""

ES = {
    # -- navigation, header, session
    "Enroll": "Registro",
    "Credentials": "Credenciales",
    "Profiles": "Perfiles",
    "Instances": "Instancias",
    "(no instances configured)": "(no hay instancias configuradas)",
    "Signed in": "Sesión iniciada",
    "Not signed in": "Sesión no iniciada",
    "Sign in": "Iniciar sesión",
    "Sign out": "Cerrar sesión",
    "Complete the sign-in in your browser…": "Complete el inicio de sesión en el navegador…",
    "Sign-in failed": "Error al iniciar sesión",
    "Not signed in. Sign in to the identity provider first.": (
        "No ha iniciado sesión. Inicie sesión primero en el proveedor de identidad."
    ),
    "The session has expired. Sign in to the identity provider again.": (
        "La sesión ha caducado. Vuelva a iniciar sesión en el proveedor de identidad."
    ),
    "Windows only lets administrators access FIDO security keys directly. Restart the "
    "application as administrator to detect and enroll keys.": (
        "Windows solo permite a los administradores acceder directamente a las llaves de "
        "seguridad FIDO. Reinicie la aplicación como administrador para detectar y "
        "registrar llaves."
    ),
    "Restart as administrator": "Reiniciar como administrador",
    "Enrollment in progress": "Registro en curso",
    "An enrollment is in progress. Cancel it and quit?": (
        "Hay un registro en curso. ¿Cancelarlo y salir?"
    ),
    # -- common
    "Error": "Error",
    "Cancel": "Cancelar",
    "Save": "Guardar",
    "Delete": "Eliminar",
    "Edit": "Editar",
    "Close": "Cerrar",
    "Refresh": "Actualizar",
    "Search": "Buscar",
    "Searching…": "Buscando…",
    "Name": "Nombre",
    "Created": "Creación",
    "Details": "Detalles",
    "ID": "ID",
    "User": "Usuario",
    "Username": "Nombre de usuario",
    "Display name": "Nombre para mostrar",
    "E-mail": "Correo electrónico",
    "Name, username or e-mail": "Nombre, nombre de usuario o correo electrónico",
    "{count} user(s) found": "Usuarios encontrados: {count}",
    "No instance": "Sin instancia",
    "Add an identity provider instance first.": (
        "Agregue primero una instancia de un proveedor de identidad."
    ),
    "(none)": "(ninguno)",
    "(optional)": "(opcional)",
    # -- enroll page
    "1. User": "1. Usuario",
    "2. Security key": "2. Llave de seguridad",
    "3. Enrollment options": "3. Opciones de registro",
    "Profile": "Perfil",
    "Key display name": "Nombre visible de la llave",
    "e.g. YubiKey 5 NFC": "p. ej., YubiKey 5 NFC",
    "Enroll security key": "Registrar llave",
    "No security key detected": "No se detectó ninguna llave de seguridad",
    "Insert a security key or place it on the NFC reader.": (
        "Inserte una llave de seguridad o colóquela sobre el lector NFC."
    ),
    "PIN is set": "PIN establecido",
    "No PIN set": "Sin PIN",
    "minimum PIN length {length}": "longitud mínima del PIN: {length}",
    "always UV enabled": "«exigir siempre verificación (UV)» activado",
    "Enterprise Attestation enabled": "atestación Enterprise activada",
    "PIN change required": "cambio de PIN obligatorio",
    "no support for advanced options": "no admite opciones avanzadas",
    "Sign in to the identity provider first.": (
        "Inicie sesión primero en el proveedor de identidad."
    ),
    "No user": "Ningún usuario seleccionado",
    "Search for a user and select one from the list.": (
        "Busque un usuario y selecciónelo en la lista."
    ),
    "No security key": "Sin llave de seguridad",
    "Confirm enrollment": "Confirmar el registro",
    "User: {user}": "Usuario: {user}",
    "Security key: {key}": "Llave de seguridad: {key}",
    "The key will be factory reset. All FIDO credentials on it will be erased.": (
        "La llave se restablecerá a los valores de fábrica. Se borrarán todas las "
        "credenciales FIDO que contiene."
    ),
    "Cancelling…": "Cancelando…",
    "Enrollment failed": "Error en el registro",
    # -- profile options
    "Factory reset the security key": "Restablecer la llave a los valores de fábrica",
    "Erases all FIDO credentials and the PIN on the key.": (
        "Borra de la llave todas las credenciales FIDO y el PIN."
    ),
    "Set new random PIN": "Establecer un nuevo PIN aleatorio",
    "Random PIN length": "Longitud del PIN aleatorio",
    "Minimum PIN length": "Longitud mínima del PIN",
    "Force PIN change before use": "Obligar a cambiar el PIN antes del primer uso",
    "Require always UV": "Exigir siempre la verificación del usuario (UV)",
    "The key asks for the PIN on every use.": "La llave pide el PIN en cada uso.",
    "Require Enterprise Attestation": "Exigir atestación Enterprise",
    # -- profiles page
    "New profile": "Nuevo perfil",
    "Profile name": "Nombre del perfil",
    "Profile settings": "Configuración del perfil",
    "Delete profile": "Eliminar perfil",
    "Delete profile '{name}'?": "¿Eliminar el perfil «{name}»?",
    "A profile with this name already exists.": "Ya existe un perfil con este nombre.",
    "Profile name cannot be empty.": "El nombre del perfil no puede estar vacío.",
    "Minimum PIN length must be between 4 and 63.": (
        "La longitud mínima del PIN debe estar entre 4 y 63."
    ),
    "Random PIN length must be between 4 and 63.": (
        "La longitud del PIN aleatorio debe estar entre 4 y 63."
    ),
    "Random PIN length cannot be shorter than the minimum PIN length.": (
        "El PIN aleatorio no puede ser más corto que la longitud mínima del PIN."
    ),
    # -- credentials page
    "FIDO credentials of the selected user": "Credenciales FIDO del usuario seleccionado",
    "Delete selected": "Eliminar selección",
    "Delete credential": "Eliminar credencial",
    "Delete credential '{name}' of {user}? The user will no longer be able to sign in "
    "with this key.": (
        "¿Eliminar la credencial «{name}» de {user}? El usuario ya no podrá iniciar "
        "sesión con esta llave."
    ),
    "{provider} does not offer an API for listing or deleting credentials. Manage them "
    "in the provider's admin console.": (
        "{provider} no ofrece una API para enumerar ni eliminar credenciales. "
        "Adminístrelas en la consola de administración del proveedor."
    ),
    # -- instances page and dialog
    "Identity provider instances": "Instancias de proveedores de identidad",
    "Each instance is one tenant of an identity provider. Add as many as you need and "
    "switch between them with the selector at the top.": (
        "Cada instancia es un inquilino (tenant) de un proveedor de identidad. Agregue "
        "tantas como necesite y cambie de una a otra con el selector de la parte superior."
    ),
    "Add instance": "Agregar instancia",
    "Edit instance": "Editar instancia",
    "Set as active": "Establecer como activa",
    "Delete instance": "Eliminar instancia",
    "Delete instance '{name}' and its saved sign-in?": (
        "¿Eliminar la instancia «{name}» y su inicio de sesión guardado?"
    ),
    "Session": "Sesión",
    "Instance name": "Nombre de la instancia",
    "e.g. Production tenant": "p. ej., Inquilino de producción",
    "Identity provider": "Proveedor de identidad",
    "Default profile": "Perfil predeterminado",
    "Use the values of the application registered for YubiEnroll at the identity "
    "provider. The redirect URI must match the registration exactly.": (
        "Use los valores de la aplicación registrada para YubiEnroll en el proveedor de "
        "identidad. El URI de redirección debe coincidir exactamente con el del registro."
    ),
    "Instance name cannot be empty.": "El nombre de la instancia no puede estar vacío.",
    "An instance with this name already exists.": "Ya existe una instancia con este nombre.",
    "Required field is empty: {field}": "Campo obligatorio vacío: {field}",
    "The redirect URI must start with http://localhost.": (
        "El URI de redirección debe empezar por http://localhost."
    ),
    "Settings": "Configuración",
    "Language": "Idioma",
    # -- provider settings
    "Directory (tenant) ID": "Id. de directorio (inquilino)",
    "Application (client) ID": "Id. de aplicación (cliente)",
    "Client ID": "Id. de cliente",
    "Redirect URI": "URI de redirección",
    "Entra ID endpoint": "Punto de conexión de Entra ID",
    "Microsoft Graph endpoint": "Punto de conexión de Microsoft Graph",
    "Change only for national cloud deployments.": (
        "Cambie este valor solo para nubes nacionales."
    ),
    "Okta domain": "Dominio de Okta",
    "FIDO2 credentials are registered per domain (default or custom).": (
        "Las credenciales FIDO2 se registran por dominio (predeterminado o personalizado)."
    ),
    "Environment ID": "Environment ID",
    "Region": "Región",
    "Custom domain": "Dominio personalizado",
    "MFA policy ID": "Id. de la directiva de MFA",
    "Only if the environment uses a custom domain.": (
        "Solo si el entorno usa un dominio personalizado."
    ),
    "Leave empty to use the default MFA policy.": (
        "Déjelo vacío para usar la directiva de MFA predeterminada."
    ),
    "Tenant": "Tenant",
    "Realm": "Realm",
    "Journey name": "Nombre del journey",
    "WebAuthn origin": "Origen de WebAuthn",
    "The WebAuthn registration journey created for YubiEnroll.": (
        "El journey de registro de WebAuthn creado para YubiEnroll."
    ),
    "Leave empty to use the tenant address.": (
        "Déjelo vacío para usar la dirección del tenant."
    ),
    # -- PIN dialogs
    "Security key PIN": "PIN de la llave de seguridad",
    "Enter the current PIN of the security key:": (
        "Introduzca el PIN actual de la llave de seguridad:"
    ),
    "Wrong PIN.": "PIN incorrecto.",
    "Attempts remaining: {retries}": "Intentos restantes: {retries}",
    "Show PIN": "Mostrar PIN",
    "New PIN": "Nuevo PIN",
    "Repeat PIN": "Repetir PIN",
    "Choose a PIN of at least {length} characters.": (
        "Elija un PIN de al menos {length} caracteres."
    ),
    "The PIN is too short.": "El PIN es demasiado corto.",
    "The PINs do not match.": "Los PIN no coinciden.",
    "The security key rejected this PIN (too short or too simple).": (
        "La llave de seguridad rechazó este PIN (demasiado corto o demasiado sencillo)."
    ),
    # -- result dialog
    "Enrollment complete": "Registro completado",
    "The security key has been enrolled.": "La llave de seguridad se ha registrado.",
    "Serial number": "Número de serie",
    "Temporary PIN:": "PIN temporal:",
    "The PIN you entered has been set on the key.": (
        "El PIN que introdujo se ha establecido en la llave."
    ),
    "The PIN of the key was not changed.": "El PIN de la llave no se ha cambiado.",
    "The user must change the PIN before first use.": (
        "El usuario debe cambiar el PIN antes del primer uso."
    ),
    # -- enrollment engine: progress
    "Checking sign-in and permissions…": "Comprobando el inicio de sesión y los permisos…",
    "Factory reset: remove the security key now…": (
        "Restablecimiento: retire ahora la llave de seguridad…"
    ),
    "Factory reset: insert the security key again…": (
        "Restablecimiento: vuelva a insertar la llave de seguridad…"
    ),
    "Factory reset: touch the security key to confirm…": (
        "Restablecimiento: toque la llave de seguridad para confirmar…"
    ),
    "The security key has been reset.": "La llave de seguridad se ha restablecido.",
    "Setting the PIN…": "Estableciendo el PIN…",
    "Changing the PIN…": "Cambiando el PIN…",
    "Setting the minimum PIN length to {length}…": (
        "Estableciendo la longitud mínima del PIN en {length}…"
    ),
    "Enabling 'Require always UV'…": "Activando «exigir siempre verificación (UV)»…",
    "Enabling Enterprise Attestation…": "Activando la atestación Enterprise…",
    "Requesting a registration challenge…": "Solicitando un desafío de registro…",
    "Touch the security key to create the credential…": (
        "Toque la llave de seguridad para crear la credencial…"
    ),
    "Registering the credential with the identity provider…": (
        "Registrando la credencial en el proveedor de identidad…"
    ),
    "Forcing a PIN change before first use…": (
        "Activando el cambio obligatorio de PIN antes del primer uso…"
    ),
    "Done.": "Listo.",
    # -- enrollment engine: errors
    "Enrollment cancelled.": "Registro cancelado.",
    "No security key detected. Insert a key and try again.": (
        "No se detectó ninguna llave de seguridad. Inserte una llave e inténtelo de nuevo."
    ),
    "The selected security key is no longer connected. Refresh the list.": (
        "La llave de seguridad seleccionada ya no está conectada. Actualice la lista."
    ),
    "Timed out waiting for the security key.": (
        "Se agotó el tiempo de espera de la llave de seguridad."
    ),
    "The key was not touched in time.": "No se tocó la llave a tiempo.",
    "This security key does not support FIDO2.": "Esta llave de seguridad no admite FIDO2.",
    "This security key does not support a PIN.": "Esta llave de seguridad no admite PIN.",
    "This security key does not support 'Require always UV' (firmware 5.5+ needed).": (
        "Esta llave de seguridad no admite «exigir siempre verificación (UV)» (se "
        "necesita el firmware 5.5 o posterior)."
    ),
    "This security key does not support Enterprise Attestation.": (
        "Esta llave de seguridad no admite la atestación Enterprise."
    ),
    "This security key cannot enforce a minimum PIN length or a forced PIN change "
    "(firmware 5.5+ needed).": (
        "Esta llave de seguridad no puede imponer una longitud mínima del PIN ni un "
        "cambio obligatorio de PIN (se necesita el firmware 5.5 o posterior)."
    ),
    "The reset was not accepted. It must be confirmed within a few seconds of inserting "
    "the key.": (
        "No se aceptó el restablecimiento. Debe confirmarse a los pocos segundos de "
        "insertar la llave."
    ),
    "Factory reset failed.": "Error al restablecer los valores de fábrica.",
    "The current PIN is shorter than the minimum PIN length of the profile. Enable 'Set "
    "new random PIN' or 'Factory reset'.": (
        "El PIN actual es más corto que la longitud mínima del PIN del perfil. Active "
        "«Establecer un nuevo PIN aleatorio» o el restablecimiento de fábrica."
    ),
    "Too many wrong PIN attempts. Re-insert the key and try again.": (
        "Demasiados intentos de PIN incorrectos. Vuelva a insertar la llave e inténtelo "
        "de nuevo."
    ),
    "The PIN is blocked. The key must be factory reset.": (
        "El PIN está bloqueado. Hay que restablecer la llave a los valores de fábrica."
    ),
    "This security key is already registered for this user.": (
        "Esta llave de seguridad ya está registrada para este usuario."
    ),
    "The identity provider returned an RP ID that does not match its origin.": (
        "El proveedor de identidad devolvió un RP ID que no coincide con su origen."
    ),
    "The security key reported an error: {detail}": (
        "La llave de seguridad notificó un error: {detail}"
    ),
    "The credential was registered, but forcing a PIN change failed: {detail}": (
        "La credencial se registró, pero no se pudo activar el cambio obligatorio de "
        "PIN: {detail}"
    ),
    # -- bulk enrollment
    "Bulk enrollment": "Registro masivo",
    "User list": "Lista de usuarios",
    "Text or CSV file with one user per line: user name, login or e-mail. In a CSV with "
    "several columns, name the user column 'username'.": (
        "Archivo de texto o CSV con un usuario por línea: nombre de usuario, inicio de "
        "sesión o correo electrónico. En un CSV con varias columnas, llame «username» a "
        "la columna del usuario."
    ),
    "Load from file…": "Cargar desde archivo…",
    "Load user list": "Cargar lista de usuarios",
    "User lists (*.csv *.txt);;All files (*)": (
        "Listas de usuarios (*.csv *.txt);;Todos los archivos (*)"
    ),
    "No users were found in this file.": "No se encontró ningún usuario en este archivo.",
    "Clear list": "Vaciar lista",
    "Looking up users in the directory…": "Buscando usuarios en el directorio…",
    "Load a user list to begin.": "Cargue una lista de usuarios para empezar.",
    "Ready. Insert the first security key and press Start.": (
        "Listo. Inserte la primera llave de seguridad y pulse Iniciar."
    ),
    "This list belongs to another instance. Export the results and clear it.": (
        "Esta lista pertenece a otra instancia. Exporte los resultados y vacíela."
    ),
    "Enrollment options": "Opciones de registro",
    "Add the serial number to the key name": (
        "Agregar el número de serie al nombre de la llave"
    ),
    "Show PINs in the list": "Mostrar los PIN en la lista",
    "Start": "Iniciar",
    "Stop": "Detener",
    "Retry failed": "Reintentar fallidos",
    "Export results…": "Exportar resultados…",
    "Export results": "Exportar resultados",
    "Export": "Exportar",
    "The file will contain the temporary PINs in plain text. Store it securely and delete "
    "it once the keys have been handed out.": (
        "El archivo contendrá los PIN temporales en texto sin cifrar. Guárdelo de forma "
        "segura y elimínelo una vez entregadas las llaves."
    ),
    "Results exported to {path}": "Resultados exportados a {path}",
    "Unsaved PINs": "PIN sin guardar",
    "The temporary PINs have not been exported and will be lost. Continue?": (
        "Los PIN temporales no se han exportado y se perderán. ¿Continuar?"
    ),
    "Start bulk enrollment": "Iniciar el registro masivo",
    "{count} security key(s) will be enrolled, one per user.": (
        "Llaves de seguridad que se registrarán: {count} (una por usuario)."
    ),
    "Every inserted key will be factory reset. All FIDO credentials on it will be erased.": (
        "Cada llave insertada se restablecerá a los valores de fábrica. Se borrarán todas "
        "las credenciales FIDO que contenga."
    ),
    "Bulk enrollment paused": "Registro masivo en pausa",
    "{count} ready": "listos: {count}",
    "{count} enrolled": "registrados: {count}",
    "{count} failed": "con error: {count}",
    "{count} not found": "no encontrados: {count}",
    "Checking…": "Comprobando…",
    "Ready": "Listo",
    "Not found": "No encontrado",
    "In progress": "En curso",
    "Enrolled": "Registrado",
    "Failed": "Error",
    "Status": "Estado",
    "Key name": "Nombre de la llave",
    "Temporary PIN": "PIN temporal",
    "Enrolled at": "Fecha de registro",
    "Message": "Mensaje",
    "Insert the security key for {user}…": "Inserte la llave de seguridad de {user}…",
    "Remove the previous key, then insert the key for {user}…": (
        "Retire la llave anterior y, a continuación, inserte la llave de {user}…"
    ),
    "Several security keys are connected. Leave only one connected.": (
        "Hay varias llaves de seguridad conectadas. Deje conectada solo una."
    ),
    "Batch finished.": "Lote finalizado.",
    "Security key {serial} was already enrolled in this batch.": (
        "La llave de seguridad {serial} ya se registró en este lote."
    ),
    # -- key details and naming
    "Firmware": "Firmware",
    "Ready to enroll.": "Lista para registrar.",
    "serial number not readable": "no se puede leer el número de serie",
    "Key will be registered as: {name}": "La llave se registrará como: {name}",
    "Key name: {name}": "Nombre de la llave: {name}",
    # -- profile summary
    "factory reset": "restablecimiento de fábrica",
    "no factory reset": "sin restablecimiento de fábrica",
    "random PIN of {length} digits": "PIN aleatorio de {length} dígitos",
    "PIN entered by the operator": "PIN introducido por el operador",
    "forced PIN change": "cambio de PIN obligatorio",
    "always UV": "exigir siempre verificación (UV)",
    "Enterprise Attestation": "atestación Enterprise",
    # -- appearance
    "Appearance": "Apariencia",
    "Light": "Claro",
    "Dark": "Oscuro",
    "Custom": "Personalizado",
    "Custom colours": "Colores personalizados",
    "Accent colour…": "Color de énfasis…",
    "Choose the accent colour": "Elegir el color de énfasis",
    "Restart the application to apply the change.": (
        "Reinicie la aplicación para aplicar el cambio."
    ),
    "Version {version}": "Versión {version}",
    # -- hand-over to the user
    "Pass it on to the user": "Entregar al usuario",
    "The message contains the PIN. Send it through a different channel than the key "
    "itself.": (
        "El mensaje contiene el PIN. Envíelo por un canal distinto al de la propia llave."
    ),
    "Copy PIN": "Copiar PIN",
    "Copy message": "Copiar mensaje",
    "E-mail draft…": "Borrador de correo…",
    "Save to file…": "Guardar en archivo…",
    "Save message": "Guardar mensaje",
    "Text files (*.txt)": "Archivos de texto (*.txt)",
    "Copied. The clipboard will be cleared in one minute.": (
        "Copiado. El portapapeles se vaciará dentro de un minuto."
    ),
    "Saved to {path}. The file contains the PIN.": (
        "Guardado en {path}. El archivo contiene el PIN."
    ),
    "The PIN is not stored anywhere. It is shown only in this window.": (
        "El PIN no se guarda en ningún sitio. Solo se muestra en esta ventana."
    ),
    "No e-mail address is known for this user.": (
        "No se conoce ninguna dirección de correo electrónico de este usuario."
    ),
    "A draft was opened in your e-mail program. Review it and send it.": (
        "Se abrió un borrador en su programa de correo. Revíselo y envíelo."
    ),
    "No e-mail program is available. Copy the message instead.": (
        "No hay ningún programa de correo disponible. Copie el mensaje en su lugar."
    ),
    "security key": "llave de seguridad",
    "(provided separately)": "(se comunica por separado)",
    "You will be asked to set your own PIN the first time you use the key.": (
        "La primera vez que use la llave se le pedirá que establezca su propio PIN."
    ),
    "Message for the user…": "Mensaje para el usuario…",
    "Select an enrolled user to copy, e-mail or save the hand-over message.": (
        "Seleccione un usuario registrado para copiar, enviar por correo o guardar el "
        "mensaje de entrega."
    ),
    # -- export options
    "CSV files (*.csv)": "Archivos CSV (*.csv)",
    "Enrolled users only": "Solo usuarios registrados",
    "All users on the list, with their status": (
        "Todos los usuarios de la lista, con su estado"
    ),
    "Include temporary PINs": "Incluir los PIN temporales",
    "CSV, semicolon separated": "CSV separado por punto y coma",
    "CSV, comma separated": "CSV separado por comas",
    "Format": "Formato",
    # -- settings page
    "Colour scheme": "Combinación de colores",
    "Same as the system (light or dark)": "Igual que el sistema (claro u oscuro)",
    "Same as the system": "Igual que el sistema",
    "Message for the user": "Mensaje para el usuario",
    "Used after an enrollment for the e-mail draft, the copied message and the saved "
    "file. Placeholders: {placeholders}.": (
        "Se usa después de un registro para el borrador de correo, el mensaje copiado y "
        "el archivo guardado. Campos disponibles: {placeholders}."
    ),
    "Subject": "Asunto",
    "Text": "Texto",
    "Restore the default text": "Restaurar el texto predeterminado",
    "Saved.": "Guardado.",
    "The default text has been restored.": "Se ha restaurado el texto predeterminado.",
    "About": "Acerca de",
    "Version": "Versión",
    "License": "Licencia",
    "Project page": "Página del proyecto",
    "Documentation": "Documentación",
    "KeyEnroll is an independent open-source project. It is not affiliated with or "
    "endorsed by Yubico, Microsoft, Okta or Ping Identity.": (
        "KeyEnroll es un proyecto independiente de código abierto. No está afiliado a "
        "Yubico, Microsoft, Okta ni Ping Identity, ni cuenta con su respaldo."
    ),
    "Open the folder with settings and logs": "Abrir la carpeta de configuración y registros",
    # -- unexpected errors
    "An unexpected error occurred:": "Se produjo un error inesperado:",
    "Details were written to the log: {path}": (
        "Los detalles se escribieron en el archivo de registro: {path}"
    ),
    "The settings file could not be read and was set aside as {path}. KeyEnroll started "
    "with default settings.": (
        "No se pudo leer el archivo de configuración y se apartó como {path}. KeyEnroll "
        "se inició con la configuración predeterminada."
    ),
    # -- updates
    "Check for updates": "Buscar actualizaciones",
    "Checking for updates…": "Buscando actualizaciones…",
    "Open the download page": "Abrir la página de descarga",
    "Version {latest} is available (you have {current}).": (
        "La versión {latest} está disponible (tiene la {current})."
    ),
    "You have the latest version ({current}).": "Tiene la versión más reciente ({current}).",
    "Could not reach the update server. Check the connection.": (
        "No se pudo conectar con el servidor de actualizaciones. Compruebe la conexión."
    ),
    "No published release was found.": "No se encontró ninguna versión publicada.",
    "The update server is busy. Try again in a few minutes.": (
        "El servidor de actualizaciones está ocupado. Inténtelo de nuevo en unos minutos."
    ),
    "The update server returned an unexpected answer.": (
        "El servidor de actualizaciones devolvió una respuesta inesperada."
    ),
}
