from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import pandas as pd
import io
import logging


_logger = logging.getLogger(__name__)

class ImportadorClientesWizards(models.TransientModel):
    _name = 'importador.clientes.wizard'
    _description = 'Asistente para importar clientes desde CSV'

    archivo_csv = fields.Binary(
        string = 'Archivo CSV',
        required = True,
        help = 'Selecciona el archivo CSV con los clientes'
    )

    nombre_archivo = fields.Char(string='Nombre del archivo')


    #Pedimos el separador obligatorio
    separador = fields.Selection([
        (',','Coma(,)'),
        (';','Punto y coma (;)'),
        ('\\t','Tabulador'),
    ], string='Separador',default=',', required = True)

    #Esto para que no haya ningun cliente con informacion que sea del encabezado(name, email, etc)
    tiene_encabezados = fields.Boolean(string='Tiene encabezados', default=True, help='Si la primera fila tiene los nombres de las columnas o no')

    tamanio_lote = fields.Selection([
        ('50', '50 clientes por lote (mas seguro)'),
        ('100', '100 clientes por lote (recomendado)'),
        ('250', '250 clientes por lote (rapido)'),
        ('500', '500 clientes por lote (para archivos grandes)')
    ], string='Tamaño de lote', default='100', required=True)


    #Mostrara informacion de resultados
    resultado = fields.Text(string='Resultado', readonly=True)



    def _leer_csv(self):
        ''' 
        Funcion que lee archivos .CSV
        '''
        if not self.archivo_csv:
            raise UserError('Debes seleccionar un archivo CSV')

        # Validar que el archivo sea .csv
        if self.nombre_archivo and not self.nombre_archivo.lower().endswith('.csv'):
            raise UserError(f'El archivo "{self.nombre_archivo}" no es un CSV. Por favor subí un archivo con extensión .csv')

        # Modo sin encabezados no soportado
        if not self.tiene_encabezados:
            raise UserError('El modo sin encabezados no está soportado. Asegurate de que tu CSV tenga una primera fila con los nombres de columnas (nombre, email, teléfono).')


        try:
            #Decodificamos el archivo(necesario para poder leerlo)
            contenido = base64.b64decode(self.archivo_csv)

            #Leemos el csv como un dataframe con estos parametros
            df = pd.read_csv(
                io.BytesIO(contenido), #El contenido lo guardamos en memoria volatil
                sep=self.separador,
                header=0 if self.tiene_encabezados else None,
                encoding='utf-8-sig',
                dtype=str #Lo leemos todo como un string
            )

            _logger.info(f"Se leyo {len(df)} filas, columnas: {df.columns.tolist()}")

            #Retornamos el dataframe
            return df

        except Exception as e:
            raise UserError(f'Error al leer el CSV: {str(e)}')



    def _encontrar_columna(self, df, posibles_nombres: list):
        '''
        Busca posibles nombres dentro de las columnas del CSV
        Retorna el nombre de la columna encontrada o None
        '''
        encontrado = None 
        
        # Busqueda exacta
        for nombre in posibles_nombres:
            if nombre in df.columns and not encontrado:
                encontrado = nombre
        
        # Busqueda case-insensitive
        if not encontrado:
            for nombre in posibles_nombres:
                for col in df.columns:
                    if col.lower() == nombre.lower() and not encontrado:
                        encontrado = col
        
        return encontrado


    def _generar_recomendacion(self, total_filas: int) -> str:

        '''
            Esta funcion genera la recomendacion basada en el tamaño de filas
        '''

        if total_filas < 1000:
            return "Puede importar directamente"

        elif total_filas < 5000:
            return "Recomendamos lotes de 100"
        
        elif total_filas < 10000:
            return "Recomendamos lotes de 250 y cuidado"

        else:
            return "Usar lotes de 500 y hacer backup"



    def action_previsalizar(self):
        '''
            Funcion que previsualiza los datos a guardar, duplicados y analisis de esos datos
        '''
        
        #Leemos el archivo csv:
        df = self._leer_csv()

        #Buscamos si hay columnas de tipo email, correo o mail
        col_email = self._encontrar_columna(df,['email', 'correo', 'mail'])

        #Buscamos si hay columnas de tipo nombre, name, cliente, nombre_completo o full_name
        col_nombre = self._encontrar_columna(df,['nombre', 'name', 'nombre_completo','full_name' ])

        #Buscamos si hay columnas de tipo telefono, phone, celular o movil
        col_telefono = self._encontrar_columna(df,['telefono', 'phone', 'celular', 'movil'])


        #Preparamos el mensaje super simple:
        lineas = []
        lineas.append("Vista previa: ")
        lineas.append("======================")
        lineas.append(f"Total de filas: {len(df)}")
        lineas.append("")

        #Analizamos mails
        if col_email:
            emails = df[col_email].astype(str).str.strip()
            validos = emails[emails.str.contains('@', na=False)].count()
            lineas.append(f"Emails validos: {validos}/{len(df)}")
        else:
            lineas.append("Columna email no detectada")


        #Analizamos Nombres
        if col_nombre:
            nombres = df[col_nombre].astype(str).str.strip()
            completos = nombres[~nombres.isin(['','nan','None'])].count()
            lineas.append(f"Nombres completos: {completos}/{len(df)}")
        else:
            lineas.append(f"Columna nombres no detectada")


        #Analizamos telefonos
        if col_telefono:
            telefonos = df[col_telefono].astype(str).str.strip()
            tienen_telefono = telefonos[~telefonos.isin(['','nan','None'])].count()
            lineas.append(f"Con telefono: {tienen_telefono}/{len(df)}")
        else:
            lineas.append("Columna telefono no detectada")


        lineas.append("")
        lineas.append("Aprete el boton IMPORTAR")

        self.resultado = "\n".join(lineas)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'importador.clientes.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }



    def importar(self):
        '''
            Funcion que importa los clientes del csv a Odo.
        '''

        #Leemos el archivo 
        df = self._leer_csv()

        #Identificamos las columnas nombre, email, telefono
        col_email = self._encontrar_columna(df, ['email', 'correo', 'mail'])
        col_nombre = self._encontrar_columna(df, ['nombre', 'name', 'nombre_completo', 'full_name'])
        col_telefono = self._encontrar_columna(df, ['telefono', 'phone', 'celular', 'movil'])

        if not col_email and not col_telefono:
            raise UserError("No hay columna de email ni telefono. Se requiere al menos un contacto.")

        #Usaremos el tamaño del lote que el usuario ha elegido
        batch_size = int(self.tamanio_lote)

        total_filas = len(df)
        total_lotes = (total_filas + batch_size - 1) // batch_size

        creados = 0
        actualizados = 0
        errores = []
        advertencias = []

        for lote_num in range(total_lotes):
            inicio = lote_num * batch_size
            fin = min(inicio + batch_size, total_filas)
            lote = df.iloc[inicio:fin]
            
            procesados_en_lote = {
                'emails': {},
                'telefonos': {}
            }

            for idx, fila in lote.iterrows():
                procesar = True
                vals = {}
                mensajes_fila = []

                # ===========================================
                # MANEJO DE NOMBRE
                # ===========================================
                nombre_original = ''
                if col_nombre:
                    nombre_raw = fila[col_nombre]
                    if pd.notna(nombre_raw) and nombre_raw is not None:
                        nombre_original = str(nombre_raw).strip()
                        if nombre_original.lower() in ['nan', 'none', '']:
                            nombre_original = ''
                    else:
                        nombre_original = ''

                if nombre_original:
                    vals['name'] = nombre_original[:100]
                else:
                    # Intentar generar nombre desde email
                    nombre_generado = False
                    if col_email:
                        email_raw = fila[col_email]
                        if pd.notna(email_raw) and email_raw is not None:
                            email_str = str(email_raw).strip().lower()
                            if email_str and '@' in email_str:
                                # Parte local del email
                                local = email_str.split('@')[0]
                                _logger.warning(f"DEBUG: local type = {type(local)}, valor = {local}")
                                local_str = str(local)
                                local_limpio = local_str.replace('.', ' ').replace('_', ' ').title()
                                if local_limpio:
                                    vals['name'] = local_limpio[:100]
                                    mensajes_fila.append(f"Nombre generado: '{local_limpio}'")
                                    nombre_generado = True

                    if not nombre_generado:
                        vals['name'] = "Contacto sin nombre"
                        mensajes_fila.append("Nombre no disponible")

                # ===========================================
                # MANEJO DE EMAIL
                # ===========================================
                if col_email:
                    email_raw = fila[col_email]
                    if pd.notna(email_raw) and email_raw is not None:
                        email = str(email_raw).strip()
                        email_lower = email.lower()
                        
                        if email_lower and '@' in email_lower:
                            vals['email'] = email
                        elif email_lower:
                            mensajes_fila.append(f"Email invalido: {email}")
                    else:
                        # Es NaN o None
                        pass

                # ===========================================
                # MANEJO DE TELÉFONO
                # ===========================================
                if col_telefono:
                    telefono_raw = fila[col_telefono]
                    if pd.notna(telefono_raw) and telefono_raw is not None:
                        telefono = str(telefono_raw).strip()
                        if telefono and telefono.lower() not in ['nan', 'none', '']:
                            telefono_limpio = ''.join(c for c in telefono if c.isdigit() or c == '+')
                            if telefono_limpio:
                                vals['phone'] = telefono_limpio[:15]
                            else:
                                mensajes_fila.append(f"Telefono invalido: '{telefono}'")

                # ===========================================
                # VERIFICAR DATOS MÍNIMOS
                # ===========================================
                if not vals.get('email') and not vals.get('phone'):
                    errores.append(f"Fila {idx+2}: Sin email ni telefono validos. {', '.join(mensajes_fila)}")
                    procesar = False

                # ===========================================
                # VERIFICAR DUPLICADOS EN LOTE
                # ===========================================
                if procesar:
                    email = vals.get('email')
                    telefono = vals.get('phone')
                    
                    if email and email in procesados_en_lote['emails']:
                        mensajes_fila.append("Duplicado en archivo (mismo email, omitido)")
                        procesar = False
                    elif telefono and telefono in procesados_en_lote['telefonos']:
                        mensajes_fila.append("Duplicado en archivo (mismo telefono, omitido)")
                        procesar = False

                # ===========================================
                # PROCESAR EN ODOO
                # ===========================================
                if procesar:
                    try:
                        partner = False
                        email = vals.get('email')
                        telefono = vals.get('phone')
                        
                        # Buscar por email
                        if email:
                            partner = self.env['res.partner'].search([
                                ('email', '=', email)
                            ], limit=1)
                        
                        # Buscar por teléfono si no se encontró
                        if not partner and telefono:
                            partner = self.env['res.partner'].search([
                                ('phone', '=', telefono)
                            ], limit=1)
                        
                        if partner:
                            partner.write(vals)
                            actualizados += 1
                            if email:
                                procesados_en_lote['emails'][email] = partner
                            if telefono:
                                procesados_en_lote['telefonos'][telefono] = partner
                        else:
                            partner_nuevo = self.env['res.partner'].create(vals)
                            creados += 1
                            if email:
                                procesados_en_lote['emails'][email] = partner_nuevo
                            if telefono:
                                procesados_en_lote['telefonos'][telefono] = partner_nuevo
                        
                        if mensajes_fila:
                            advertencias.append(f"Fila {idx+2}: {', '.join(mensajes_fila)}")
                            
                    except Exception as e:
                        errores.append(f"Fila {idx+2}: Error al guardar - {str(e)}")
                
                elif mensajes_fila:
                    # Registrar advertencias de filas no procesadas
                    advertencias.append(f"Fila {idx+2}: {', '.join(mensajes_fila)}")
            
            self.env.cr.commit()
        
        # ===========================================
        # REPORTE FINAL
        # ===========================================
        mensaje = f"""
    IMPORTACION COMPLETADA
    =======================
    Total filas: {total_filas}
    Lotes: {total_lotes} (tamaño {batch_size})
    Creados: {creados}
    Actualizados: {actualizados}
    Advertencias: {len(advertencias)}
    Errores: {len(errores)}
        """
        
        if advertencias:
            mensaje += "\n\nADVERTENCIAS (primeras 5):\n"
            for adv in advertencias[:5]:
                mensaje += f"  - {adv}\n"
        
        if errores:
            mensaje += "\n\nERRORES (primeros 5):\n"
            for err in errores[:5]:
                mensaje += f"  - {err}\n"
        
        self.resultado = mensaje
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Importacion completada',
                'message': f'Creados: {creados}  |  Actualizados: {actualizados}  |  Advertencias: {len(advertencias)}  |  Errores: {len(errores)}',
                'type': 'success' if not errores else 'warning',
                'sticky': True,
                'next': {
                    'type': 'ir.actions.act_window',
                    'name': 'Contactos',
                    'res_model': 'res.partner',
                    'view_mode': 'list,form',
                    'views': [(False, 'list'), (False, 'form')],
                    'target': 'current',
                    'context': {'search_default_customer_rank': 1},
                }
            }
        }