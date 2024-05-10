import streamlit as st
import pandas as pd
import json
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt


def fetch_tickets(url, params, auth):
    response = requests.get(url, params=params, auth=auth)
    return response.json()

#Usada para test
def save_json(data, filename):
    """
    Guarda los datos en formato JSON en un archivo local.
    :param data: Datos en formato JSON a guardar.
    :param filename: Nombre del archivo donde se guardarán los datos.
    """
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
    print(f"Datos guardados en {filename}")

def process_data(data):
    results = []
    if 'results' in data:
        for result in data['results']:
            if all(key in result for key in ['url', 'subject', 'description']):
                ticket_number = result['url'].split('/')[-1].split('.')[0]
                results.append({
                    "ticket": ticket_number,
                    "subject": result['subject'],
                    "description": result['description']
                })
    return pd.DataFrame(results)

def call_openai_api(data, headers):
    url = 'https://api.openai.com/v1/chat/completions'
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_message(subject, description):
    return {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "Analiza la categoría, urgencia y sentimiento del siguiente ticket. Responde con tres palabras que representen lo mejor posible tu análisis respectivamente. Por ejemplo: compra asistida, alta prioridad, neutro."
            },
            {
                "role": "user",
                "content": f"Asunto: {subject}, Comentario: {description}"
            }
        ]
    }

def analyze_tickets(df, headers):
    for index, row in df.iterrows():
        message = create_message(row['subject'], row['description'])
        response = call_openai_api(message, headers)
        if 'choices' in response and response['choices']:
            df.at[index, 'response'] = response['choices'][0].get('message', {}).get('content', 'No content available')
        else:
            df.at[index, 'response'] = 'No response'
    return df


def create_and_show_wordcloud(df, column='response'):
    if column in df.columns:
        # Preprocesamiento básico: convertir a minúsculas
        text = " ".join(str(desc).lower() for desc in df[column] if isinstance(desc, str))

        # Generar y mostrar la nube de palabras
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.show()
    else:
        print(f"Error: La columna '{column}' no existe en el DataFrame.")

#Usada para test
#Guardar el dataframe a csv para revisar
def save_dataframe_to_csv(df, filename):
    df.to_csv(filename, index=False)  # index=False para no guardar el índice del DataFrame


# Streamlit app
def main():
    st.title('Dashboard SuperMarket 23')
    st.write("Esta es visualización es generada a partir Insigths obtenidos de ChatGPT.")

    # Lista de opciones para la lista desplegable
    status_options = ['new', 'open', 'closed', 'pending', 'resolved']

    # Crear una lista desplegable y asignar la selección a una variable
    selected_status = st.selectbox('Seleccione el estado del ticket:', status_options)

    # Puedes usar `selected_status` en tu aplicación, por ejemplo:
    #st.write(f"El estado del ticket seleccionado es: {selected_status}")

    # Configuration and parameters
    url = 'https://callcentertreew.zendesk.com/api/v2/search.json'
    params = {'query': f'type:ticket status:{selected_status}', 'sort_by': 'created_at', 'sort_order': 'asc'}
    #params = {'query': 'type:ticket status:''user_input', 'sort_by': 'created_at', 'sort_order': 'asc'}
    auth = ('chat_account8@treew.com/token', 'token de Zendesk')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer Aqui va el token de openai'}

    if st.button('Cargar y Procesar los datos'):
        st.set_option('deprecation.showPyplotGlobalUse', False)  # Opción para evitar una advertencia en Streamlit

        # Indicador de progreso
        st.write("Obteniendo datos de los tickets...")
        progress_bar = st.progress(0)
        # Obtener de la API de Zendesk, en el enpoint search los tickets con estado nuevo
        ticket_data = fetch_tickets(url, params, auth)

        st.write("Procesando los datos de los tickets...")
        #Sacar los campos ticket, asunto y el comentario
        df = process_data(ticket_data)
        progress_bar.progress(25)  # Actualizar el progreso a 25%

        st.write("Analizando los tickets...")
        # Analyze tickets con chagpt version 3.5 turbo
        df = analyze_tickets(df, headers)
        progress_bar.progress(50)  # Actualizar el progreso a 50%

        st.write("Creando visualización de la nube de palabras...")
        #Plot de gráfico de nubes
        create_and_show_wordcloud(df)

        st.pyplot()  # Mostrar la figura en la interfaz de Streamlit
        progress_bar.progress(100)  # Completa el progreso

        st.success('Visualización completada con éxito!')

if __name__ == '__main__':
    main()
