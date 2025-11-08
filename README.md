# Backlink Checker Automatizado

Un script de Python para encontrar posibles backlinks de uno o varios dominios utilizando el motor de búsqueda Bing. La herramienta simula ser un navegador real usando Selenium y automatiza la búsqueda a través de una lista de "dorks" comunes para maximizar los resultados.

## Características

- **Búsqueda Automatizada:** Itera automáticamente sobre una lista de 10 dorks de búsqueda efectivos para encontrar una amplia gama de backlinks.
- **Análisis Masivo:** Escanea una lista de dominios desde un archivo de texto para un análisis eficiente a gran escala.
- **Simulación de Navegador Real:** Utiliza Selenium y un navegador Chrome en modo headless para evitar bloqueos comunes de web scraping.
- **Limpieza de URLs:** Decodifica y limpia las URLs de redirección de Bing para mostrar los enlaces de destino reales.
- **Filtrado Inteligente:** Excluye automáticamente los dominios propios y los de Bing para una lista de resultados más limpia.

## Requisitos

- Python 3.6+
- El navegador Google Chrome instalado en tu sistema.

## Instalación

1.  **Clona o descarga este repositorio.**

2.  **Crea un entorno virtual (recomendado):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # En Windows: .\.venv\Scripts\activate
    ```

3.  **Instala las dependencias necesarias:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Nota: Primero necesitarás crear el archivo `requirements.txt` ejecutando `pip freeze > requirements.txt` después de instalar las librerías manualmente si aún no lo has hecho).*


## Uso

La herramienta se puede utilizar de dos maneras:

### 1. Analizar un solo dominio

Proporciona el dominio como un argumento directo al script.

**Ejemplo:**
```bash
python backlink_checker.py dragonjar.org
```

### 2. Analizar múltiples dominios desde un archivo

Crea un archivo de texto (ej. `dominios.txt`) y añade un dominio por línea:

**dominios.txt:**
```
dragonjar.org
kaslhlatam.com
google.com
```

Luego, ejecuta el script usando el flag `-f` o `--file`.

**Ejemplo:**
```bash
python backlink_checker.py -f dominios.txt
```

### Argumentos Adicionales

- `--pages <N>`: Especifica el número de páginas de resultados a analizar para *cada dork*. El valor por defecto es 1. Aumentar este número puede dar más resultados, pero también hará que el script tarde más y aumente el riesgo de bloqueo.

**Ejemplo:**
```bash
python backlink_checker.py -f dominios.txt --pages 3
```

## Nota Importante sobre Web Scraping

Esta herramienta realiza web scraping. Aunque se han tomado medidas para que parezca una interacción humana (usando Selenium y pausas), un uso excesivo o muy rápido puede resultar en un bloqueo temporal de tu dirección IP por parte de Bing. Úsala con moderación. Los resultados son una aproximación y pueden no ser tan completos como los de herramientas de SEO de pago como Semrush o Ahrefs.
