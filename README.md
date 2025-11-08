# Domain Analyzer

Una herramienta de reconocimiento de dominios en Python que combina dos funciones principales:
1.  **Buscador de Backlinks:** Encuentra backlinks potenciales utilizando el motor de búsqueda Bing con una serie de dorks automatizados.
2.  **Escáner de Wayback Machine:** Busca archivos históricos (como backups, logs, etc.) indexados en la Wayback Machine filtrando por extensiones de archivo.

La herramienta está diseñada para ser no interactiva, modular y capaz de analizar un solo dominio o una lista de dominios de forma masiva.

## Estructura de Archivos

Todos los archivos de la herramienta y sus salidas se encuentran en la carpeta `recon/`.

```
recon/
├── domain_analyzer.py       # El script principal
├── requirements.txt         # Las dependencias del proyecto
├── domains_to_scan.txt      # Un archivo de ejemplo para el análisis masivo
└── example.com_analysis.txt # Un archivo de salida de ejemplo
```

## Características

- **Doble Funcionalidad:** Realiza tanto análisis de backlinks como escaneos de archivos históricos.
- **Búsqueda Automatizada de Backlinks:** Itera automáticamente sobre una lista de 10 dorks de búsqueda efectivos.
- **Análisis Masivo:** Escanea una lista de dominios desde un archivo de texto.
- **Simulación de Navegador Real:** Utiliza Selenium para evitar bloqueos comunes.
- **Salida Consolidada:** Guarda todos los resultados de un dominio en un único archivo de texto organizado por secciones.
- **Configurable:** Permite ajustar el número de páginas a escanear y las extensiones de archivo a buscar.

## Requisitos

- Python 3.6+
- El navegador Google Chrome instalado en tu sistema.

## Instalación

1.  **Navega a la carpeta `recon`:**
    ```bash
    cd recon
    ```

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Windows: .\.venv\Scripts\activate
    ```

3.  **Instala las dependencias necesarias:**
    ```bash
    pip install -r requirements.txt
    ```

## Uso

La herramienta se ejecuta desde la línea de comandos y requiere que especifiques el tipo de escaneo.

### Argumentos Principales

-   `dominio` o `-f <archivo>`: El objetivo. Proporciona un solo dominio o un archivo con una lista de dominios (uno por línea).
-   `--scan <modo>`: **(Obligatorio)** El tipo de análisis a realizar.
    -   `backlinks`: Solo busca backlinks.
    -   `wayback`: Solo busca en la Wayback Machine.
    -   `all`: Realiza ambos análisis.
-   `--pages <N>`: (Opcional) Para el escaneo de backlinks, define el número máximo de páginas a buscar por cada dork. **Por defecto es 10.**
-   `--extensions <lista>`: (Opcional) Para el escaneo de Wayback, define las extensiones a buscar, separadas por comas. Por defecto es `.zip,.sql,.bak,.rar,.tar.gz,.7z,.old,.backup`.

### Ejemplos de Comandos

**1. Escaneo de Backlinks para un solo dominio:**
```bash
python domain_analyzer.py example.com --scan backlinks
```

**2. Escaneo de Wayback para un solo dominio con extensiones personalizadas:**
```bash
python domain_analyzer.py example.com --scan wayback --extensions ".log,.config,.env"
```

**3. Escaneo completo para una lista de dominios en un archivo:**
```bash
python domain_analyzer.py -f domains_to_scan.txt --scan all
```

**4. Escaneo completo para una lista, buscando solo en las primeras 2 páginas de backlinks:**
```bash
python domain_analyzer.py -f domains_to_scan.txt --scan all --pages 2
```

### Salida

Los resultados se guardarán en un archivo de texto nombrado `{dominio}_analysis.txt` dentro de la carpeta `recon`.

## Nota Importante

Esta herramienta realiza web scraping. Un uso excesivo o muy rápido puede resultar en un bloqueo temporal de tu dirección IP. Úsala con moderación.
