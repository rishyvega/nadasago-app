%%writefile app.py
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pyzbar.pyzbar import decode
from PIL import Image
import io
import datetime

# Configuración de página orientada a móviles
st.set_page_config(page_title="NadasaGO", layout="centered", initial_sidebar_state="collapsed")

# CSS para desactivar el pull-to-refresh en Android y estilizar componentes
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        overscroll-behavior-y: contain;
    }
    .stButton>button {
        border-radius: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# Inicializar Base de Datos Simplificada en Memoria (Session State)
if 'page' not in st.session_state: st.session_state.page = 'Menu'
if 'tiendas' not in st.session_state: st.session_state.tiendas = pd.DataFrame(columns=['Nombre', 'Lat', 'Lon'])
if 'inventario' not in st.session_state: st.session_state.inventario = pd.DataFrame(columns=['Codigo', 'Cantidad'])
if 'entregas_temp' not in st.session_state: st.session_state.entregas_temp = []
if 'historial' not in st.session_state: st.session_state.historial = pd.DataFrame(columns=['Fecha', 'Tienda', 'Codigo', 'Cantidad'])
if 'temp_click' not in st.session_state: st.session_state.temp_click = None

def go_to(page):
    st.session_state.page = page

# Encabezado Fijo de la App
st.title("📦 NadasaGO")
st.write("---")

# --- CONTROL DE BOTÓN REGRESAR GENERAL ---
if st.session_state.page != 'Menu':
    if st.button("⬅️ Volver al Menú Principal", use_container_width=True):
        st.session_state.temp_click = None  
        go_to('Menu')
        st.rerun()
    st.write("---")

# --- MÓDULO: MENÚ PRINCIPAL ---
if st.session_state.page == 'Menu':
    st.write("### Menú Principal")
    if st.button("🏬 Registrar Tienda", use_container_width=True): go_to('Tiendas')
    if st.button("📥 Dar de alta inventario", use_container_width=True): go_to('Alta_Inventario')
    if st.button("🚚 Registrar Entrega", use_container_width=True): go_to('Entrega')
    if st.button("📊 Inventarios (Stock)", use_container_width=True): go_to('Inventario')
    if st.button("📈 Tendencia y Reportes", use_container_width=True): go_to('Tendencia')

# --- MÓDULO: REGISTRAR TIENDA ---
elif st.session_state.page == 'Tiendas':
    st.header("🏬 Registrar Tienda")
    
    nombre_tienda = st.text_input("Nombre de la Nueva Tienda")
    st.write("👇 Haz clic en el mapa para situar el icono de la tienda:")
    
    m = folium.Map(location=[23.6345, -102.5528], zoom_start=5)
    
    # Mostrar tiendas guardadas con icono de tienda
    for _, row in st.session_state.tiendas.iterrows():
        folium.Marker(
            [row['Lat'], row['Lon']], 
            popup=row['Nombre'], 
            icon=folium.Icon(color='blue', icon='shopping-cart', prefix='glyphicon')
        ).add_to(m)
        
    # Vista previa del clic actual en verde
    if st.session_state.temp_click:
        folium.Marker(
            st.session_state.temp_click,
            popup="📍 Ubicación seleccionada",
            icon=folium.Icon(color='green', icon='shopping-cart', prefix='glyphicon')
        ).add_to(m)
        
    map_data = st_folium(m, height=400, width=700, key="mapa_registro")
    
    if map_data and map_data.get('last_clicked'):
        click_coords = (map_data['last_clicked']['lat'], map_data['last_clicked']['lng'])
        if st.session_state.temp_click != click_coords:
            st.session_state.temp_click = click_coords
            st.rerun()

    if st.button("💾 Guardar Tienda", use_container_width=True):
        if not nombre_tienda:
            st.error("Por favor, ingresa el nombre de la tienda.")
        elif not st.session_state.temp_click:
            st.error("Por favor, toca el mapa para ubicar la tienda.")
        else:
            lat, lon = st.session_state.temp_click
            nueva_tienda = pd.DataFrame([{'Nombre': nombre_tienda, 'Lat': lat, 'Lon': lon}])
            st.session_state.tiendas = pd.concat([st.session_state.tiendas, nueva_tienda], ignore_index=True)
            st.success(f"¡Tienda '{nombre_tienda}' registrada exitosamente!")
            st.session_state.temp_click = None 
            st.rerun()
            
    st.write("---")
    st.write("### 📝 Editar / Modificar Tiendas")
    st.session_state.tiendas = st.data_editor(st.session_state.tiendas, num_rows="dynamic", use_container_width=True)

# --- MÓDULO: DAR DE ALTA INVENTARIO ---
elif st.session_state.page == 'Alta_Inventario':
    st.header("📥 Alta de Inventario")
    
    # Escáner dual: Cámara o Entrada manual
    camara_inv = st.camera_input("📷 Escanear Código de Barras")
    codigo_manual_inv = st.text_input("✍️ O ingresa el código manualmente")
    cant_inv = st.number_input("🔢 Cantidad", min_value=1, step=1, value=1)
    
    codigo_detectado_inv = None
    if camara_inv is not None:
        img = Image.open(camara_inv)
        codigos = decode(img)
        if codigos:
            codigo_detectado_inv = codigos[0].data.decode('utf-8')
            st.success(f"✅ Código Detectado por Cámara: {codigo_detectado_inv}")
        else:
            st.warning("No se detectó código en la imagen. Intenta enfocar mejor.")
            
    if st.button("💾 Guardar en Inventario", use_container_width=True):
        codigo_final_inv = codigo_detectado_inv or codigo_manual_inv
        if codigo_final_inv:
            # Buscar coincidencia exacta de código de barras
            idx = st.session_state.inventario.index[st.session_state.inventario['Codigo'] == codigo_final_inv].tolist()
            if idx:
                st.session_state.inventario.loc[idx[0], 'Cantidad'] += cant_inv
            else:
                nuevo_item = pd.DataFrame([{'Codigo': codigo_final_inv, 'Cantidad': cant_inv}])
                st.session_state.inventario = pd.concat([st.session_state.inventario, nuevo_item], ignore_index=True)
            st.success(f"¡Código {codigo_final_inv} actualizado con +{cant_inv} unidades!")
            st.rerun()
        else:
            st.error("Debes ingresar un código de barras de forma manual o mediante la cámara.")
            
    st.write("---")
    st.write("### 📝 Modificar / Eliminar Inventario Directamente")
    st.session_state.inventario = st.data_editor(st.session_state.inventario, num_rows="dynamic", use_container_width=True)

# --- MÓDULO: REGISTRAR ENTREGA ---
elif st.session_state.page == 'Entrega':
    st.header("🚚 Registrar Entrega")
    
    if st.session_state.tiendas.empty:
        st.warning("⚠️ No existen tiendas registradas. Ve al módulo de Registrar Tienda primero.")
    else:
        tienda_seleccionada = st.selectbox("Selecciona la Tienda de Destino", st.session_state.tiendas['Nombre'].tolist())
        
        st.write("### 📷 Escaneo y Registro")
        camara_imagen = st.camera_input("Escanear Código de Barras")
        codigo_manual = st.text_input("Entrada Manual de Código")
        
        codigo_detectado = None
        if camara_imagen is not None:
            img = Image.open(camara_imagen)
            codigos = decode(img)
            if codigos:
                codigo_detectado = codigos[0].data.decode('utf-8')
                st.success(f"✅ Código Escaneado: {codigo_detectado}")
            else:
                st.warning("No se detectó código en la imagen.")
                
        if st.button("➕ Agregar Producto a la Lista", use_container_width=True):
            codigo_final = codigo_detectado or codigo_manual
            if codigo_final:
                # VALIDACIÓN 1: Verificar si el código existe en el inventario maestro
                idx = st.session_state.inventario.index[st.session_state.inventario['Codigo'] == codigo_final].tolist()
                if not idx:
                    st.error(f"❌ El item con el código '{codigo_final}' no existe en el inventario.")
                else:
                    # VALIDACIÓN 2: Verificar disponibilidad restando lo ya escaneado en esta sesión
                    cant_maestra = st.session_state.inventario.loc[idx[0], 'Cantidad']
                    ya_en_lista = st.session_state.entregas_temp.count(codigo_final)
                    
                    if cant_maestra - ya_en_lista <= 0:
                        st.error(f"⚠️ No hay inventario disponible para el código '{codigo_final}' (Stock total agotado).")
                    else:
                        st.session_state.entregas_temp.append(codigo_final)
                        st.success(f"Código {codigo_final} añadido provisionalmente.")
                        st.rerun()
            else:
                st.error("No hay código válido detectado.")
                
        if st.session_state.entregas_temp:
            st.write("---")
            st.write("**📋 Lista de Entrega (Puedes eliminar renglones aquí):**")
            
            df_entregas_edicion = pd.DataFrame(st.session_state.entregas_temp, columns=['Codigo'])
            df_editado = st.data_editor(df_entregas_edicion, num_rows="dynamic", use_container_width=True)
            st.session_state.entregas_temp = df_editado['Codigo'].dropna().tolist()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Limpiar Todo", use_container_width=True):
                    st.session_state.entregas_temp = []
                    st.rerun()
            with col2:
                if st.button("🏁 Terminar y Descontar", use_container_width=True):
                    conteo = pd.Series(st.session_state.entregas_temp).value_counts()
                    
                    for cod, qty in conteo.items():
                        idx = st.session_state.inventario.index[st.session_state.inventario['Codigo'] == cod].tolist()
                        if idx:
                            st.session_state.inventario.loc[idx[0], 'Cantidad'] -= qty
                            nuevo_hist = pd.DataFrame([{'Fecha': datetime.datetime.now(), 'Tienda': tienda_seleccionada, 'Codigo': cod, 'Cantidad': qty}])
                            st.session_state.historial = pd.concat([st.session_state.historial, nuevo_hist], ignore_index=True)
                    
                    st.session_state.entregas_temp = []
                    st.success("✅ Entrega completada y stock deducido del inventario.")
                    st.rerun()

# --- MÓDULO: INVENTARIOS ---
elif st.session_state.page == 'Inventario':
    st.header("📊 Inventario Actual (Solo Códigos)")
    st.info("💡 Haz clic en el encabezado de cualquier columna para ordenar de forma ascendente/descendente.")
    
    st.session_state.inventario = st.data_editor(st.session_state.inventario, num_rows="dynamic", use_container_width=True)

# --- MÓDULO: TENDENCIA ---
elif st.session_state.page == 'Tendencia':
    st.header("📈 Análisis de Tendencias de Salida")
    
    df_hist = st.session_state.historial.copy()
    
    if not df_hist.empty:
        df_hist['Fecha'] = pd.to_datetime(df_hist['Fecha'])
        
        periodo = st.radio("Escala de agrupación temporal:", ["Día", "Semana", "Mes", "Año"], horizontal=True)
        
        if periodo == "Día":
            df_hist['Periodo_Grafica'] = df_hist['Fecha'].dt.date
        elif periodo == "Semana":
            df_hist['Periodo_Grafica'] = df_hist['Fecha'].dt.to_period('W').astype(str)
        elif periodo == "Mes":
            df_hist['Periodo_Grafica'] = df_hist['Fecha'].dt.to_period('M').astype(str)
        else:
            df_hist['Periodo_Grafica'] = df_hist['Fecha'].dt.year
            
        filtro_item = st.selectbox("Filtrar por Código de Barras", ["Todo"] + df_hist['Codigo'].unique().tolist())
        if filtro_item != "Todo":
            df_hist = df_hist[df_hist['Codigo'] == filtro_item]
            
        resumen = df_hist.groupby('Periodo_Grafica')['Cantidad'].sum().reset_index()
        
        # Gráfica de barras vertical nativa desde cero para arriba
        st.bar_chart(resumen.set_index('Periodo_Grafica'))
        
        st.write("### 📝 Historial General Modificable")
        st.session_state.historial = st.data_editor(st.session_state.historial, num_rows="dynamic", use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            st.session_state.historial.to_excel(writer, index=False, sheet_name='Historial_NadasaGO')
        
        st.download_button(
            label="📥 Descargar Reporte en Formato Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name="Reporte_Tendencias_NadasaGO.xlsx",
            mime="application/vnd.ms-excel",
            use_container_width=True
        )
    else:
        st.info("No hay datos de consumo registrados aún para modelar la gráfica de barras.")