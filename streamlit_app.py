import streamlit as st
import pandas as pd
import json
import requests
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns


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
                "content": "Necesito una evaluación concisa del siguiente ticket en forma de tres palabras separadas "
                           "por comas que represente lo más cercano posible lo siguiente:"
                           "La categoría general del problema con una de las  palabras siguientes: "
                           " problema de pago, reclamación de producto, solicitud de información, verificación, valoración, duda, otro."
                           "La prioridad basada en la urgencia con una de las  palabras siguientes: baja, normal, alta o urgente."
                           "El sentimiento con una de las  palabras siguientes: positivo, neutral o negativo."
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

#VISUALIZACIONES
def create_and_show_wordcloud(df):
    # Crear una nube de palabras para las categorías de problemas

    categories_text = " ".join(cat for cat in df['category'])
    sentiment_text = " ".join(sent for sent in df['sentiment'])

    fig, ax = plt.subplots(1, 2, figsize=(16, 8))  # Dos subplots
    # Nube de palabras para categorías
    wordcloud_cat = WordCloud(width=400, height=400, background_color='white').generate(categories_text)
    ax[0].imshow(wordcloud_cat, interpolation='bilinear')
    ax[0].set_title('Categorías de Problemas')
    ax[0].axis("off")

    # Nube de palabras para sentimientos
    wordcloud_sent = WordCloud(width=400, height=400, background_color='white').generate(sentiment_text)
    ax[1].imshow(wordcloud_sent, interpolation='bilinear')
    ax[1].set_title('Sentimientos Expresados')
    ax[1].axis("off")
    st.pyplot()
#    plt.show()
def show_urgency_distribution(df):
    #Normalizar el text en minusculas
    df['urgency'] = df['urgency'].str.lower()

    plt.figure(figsize=(8, 4))
    sns.countplot(x='urgency', data=df)
    plt.title('Distribución de Prioridad de los Tickets')
    plt.xlabel('Prioridad')
    plt.ylabel('Número de Tickets')
#   plt.show()
    st.pyplot()

def show_sentiment_distribution(df):
    # Eliminar puntos al final de las cadenas en la columna 'sentiment' y poner todo en minuscula
    df['sentiment'] = df['sentiment'].str.replace(r'\.$', '', regex=True).str.lower()

    plt.figure(figsize=(8, 4))
    sns.countplot(x='sentiment', data=df)
    plt.title('Distribución de Sentimientos')
    plt.xlabel('Sentimiento')
    plt.ylabel('Número de Tickets')
#   plt.show()
    st.pyplot()


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
    url = 'https://{url}.zendesk.com/api/v2/search.json'
    params = {'query': f'type:ticket status:{selected_status}', 'sort_by': 'created_at', 'sort_order': 'asc'}
    #params = {'query': 'type:ticket status:''user_input', 'sort_by': 'created_at', 'sort_order': 'asc'}
    auth = ('account/token', 'Aqui va la API  KEY de zendesk')
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer Aqui va la API  KEY de chatgpt'}

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

        # Dividir la columna 'response' en tres nuevas columnas
        df[['category', 'urgency', 'sentiment']] = df['response'].str.split(',', expand=True)



        progress_bar.progress(50)  # Actualizar el progreso a 50%
        st.write("Creando visualizaciónes...")

        #Graficar
        show_urgency_distribution(df)
        show_sentiment_distribution(df)
        create_and_show_wordcloud(df)

        progress_bar.progress(100)  # Completa el progreso
        st.success('Visualización completada con éxito!')

if __name__ == '__main__':
    main()
