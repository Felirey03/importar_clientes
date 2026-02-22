# Importar Clientes CSV - Odoo 15

Este módulo permite la importación masiva de contactos (res.partner) en Odoo 15 a partir de archivos CSV. Está diseñado para ser flexible, seguro y fácil de usar, eliminando la necesidad de mapear columnas manualmente en cada importación.

## Características principales

- **Detección inteligente de columnas**: El sistema busca automáticamente encabezados como "nombre", "email", "correo", "teléfono", "celular", etc.
- **Gestión de duplicados**: Evita la creación de registros repetidos chequeando tanto en el archivo como en la base de datos de Odoo (por email o teléfono).
- **Creación y Actualización**: Si el contacto ya existe, el módulo actualiza su información en lugar de generar un duplicado.
- **Procesamiento por lotes (Batch)**: Permite elegir el tamaño del lote (50, 100, 250 o 500 registros) para asegurar la estabilidad del servidor en archivos grandes.
- **Compatibilidad con formatos**: Soporta diferentes separadores (coma, punto y coma, tabulador) y codificaciones como UTF-8 con BOM (formato estándar de exportación de Excel).
- **Previsualización**: Incluye un asistente de previsualización para analizar los datos antes de realizar la importación definitiva.

## Requisitos técnicos

- Odoo 15.0
- Módulo de Contactos (`contacts`) instalado.
- Librería de Python `pandas` instalada en el entorno de Odoo.

## Instalación

1. Copia la carpeta `importar_clientes` en tu directorio de `addons`.
2. Reinicia el servidor de Odoo.
3. Activa el modo desarrollador.
4. Ve a **Aplicaciones > Actualizar lista de aplicaciones**.
5. Busca "Importar Clientes CSV" e instálalo.

## Uso

1. Ve al menú **Contactos**.
2. Haz clic en el nuevo menú lateral **Importar Clientes CSV**.
3. Sube tu archivo y selecciona el separador correspondiente.
4. (Opcional) Usa el botón **Previsualizar** para validar los datos.
5. Haz clic en **Importar Clientes**. Al finalizar, recibirás una notificación con el resumen del proceso y serás redirigido a la lista de contactos.

## Autor
- Felipe Reynoso
