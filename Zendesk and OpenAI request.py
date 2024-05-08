import requests
import json
import pandas as pd
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt

url = 'https://callcentertreew.zendesk.com/api/v2/search.json'

params = {
    'query': 'type:ticket status:new',
    'sort_by': 'created_at',
    'sort_order': 'asc'
}

auth = ('chat_account8@treew.com/token', 'aqui va la KEY de Zendesk')

response = requests.get(url, params=params, auth=auth)

#print(response.json())

# Ruta del archivo donde deseas guardar los JSON
ruta_archivo = "D:/ZenDesk/Dev/mi_archivo.json"
ruta_nuevo_archivo = "D:/ZenDesk/Dev/nuevo_archivo.json"

# Guarda el diccionario 'response' en el archivo JSON
with open(ruta_archivo, "w") as archivo:
    json.dump(response.json(), archivo, indent=4)

print(f"El diccionario se ha guardado en {ruta_archivo}")

# Verificar si el archivo existe
try:
    with open(ruta_archivo, 'r') as archivo:
        # Cargar el contenido JSON
        datos_json = json.load(archivo)

        # Verificar si el JSON tiene la clave principal "results"
        if 'results' in datos_json:
            # Obtener la lista de resultados
            resultados = datos_json['results']

            # Crear una lista para almacenar los datos agrupados
            datos_agrupados = []

            # Iterar sobre cada resultado
            for resultado in resultados:
                # Verificar si el resultado contiene las claves necesarias
                if all(clave in resultado for clave in ['url', 'subject', 'description']):
                    # Extraer los valores correspondientes a las claves
                    url = resultado['url']
                    subject = resultado['subject']
                    description = resultado['description']

                    # Partir la URL por '/' para separar los componentes
                    parts = url.split('/')

                    # El número del ticket está en la penúltima parte, y necesitamos eliminar '.json'
                    ticket_number = parts[-1].split('.')[0]

                    # Agregar los valores extraídos a la lista de datos agrupados
                    datos_agrupados.append({
                        "ticket": ticket_number,
                        "subject": subject,
                        "description": description
                    })

            # Guardar los datos agrupados en un nuevo archivo JSON
            #nombre_nuevo_archivo = "datos_agrupados.json"
            #ruta_nuevo_archivo = os.path.join(ruta_archivo, nombre_nuevo_archivo)
            with open(ruta_nuevo_archivo, 'w') as nuevo_archivo:
                json.dump(datos_agrupados, nuevo_archivo, indent=4)

            print("Datos agrupados guardados exitosamente en:", ruta_nuevo_archivo)
        else:
            print("El archivo JSON no contiene la clave principal 'results'.")
except FileNotFoundError:
    print("El archivo no existe en la ruta especificada.")

#Función para iterar los mensajes recibidos en los ticket y ser analizados, guardandolo en un dataframe
def process_tickets(json_file):
    # Cargar el archivo JSON
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Inicializar un DataFrame para almacenar los resultados
    results = pd.DataFrame()

    # Configurar la URL y la API key de OpenAI
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {aqui va la KEY de Zendesk}'
    }

    # Procesar cada entrada en el archivo JSON
    for entry in data:
        ticket = entry['ticket']
        subject = entry['subject']
        description = entry['description']

        # Preparar mensaje con el rol de analista de datos
        message = {
            "model": "gpt-3.5-turbo",
            "messages": [{
                "role": "system",
                "content": "Tu funcióm es identificar el sentimiento general y las palabras clave más comunes en las descripciones y los comentarios de los tickets. Para prever la urgencia o la naturaleza emocional de los tickets antes de que sean revisados. Estructura tu respuesta con Sentimiento General: sentiemientos separados por ',' y Palabras clave: palabras clave separadas por ',' "
            }, {
                "role": "user",
                "content": f"El ticket del cliente contiene: \nAsunto: {subject} \nMensaje: {description}"
            }]
        }

        # Realizar consulta a ChatGPT
        response = requests.post(url, headers=headers, json=message)
        response_data = response.json()

        # Verificar si la respuesta contiene la clave 'choices'
        if 'choices' in response_data and response_data['choices']:
            content = response_data['choices'][0].get('message', {}).get('content', 'No content available')
        else:
            content = 'No response'

        # Crear una fila de DataFrame con la respuesta
        new_row = pd.DataFrame({
            'Ticket': [ticket],
            'Subject': [subject],
            'Description': [description],
            'Analyst_Response': [content]
        })

        # Concatenar la fila al DataFrame existente
        results = pd.concat([results, new_row], ignore_index=True)

        # Guardar los resultados en un archivo CSV
     #results.to_csv('output_responses.csv', index=False)
     #results.to_csv('output_responses.csv', mode='a', header=not os.path.exists('output_responses.csv'), index=False)
    return results
# Ejemplo de cómo llamar a la función
df = process_tickets(ruta_nuevo_archivo)

# Concatenar todos los textos de la columna 'Analyst_Response'
text = " ".join(response for response in df.Analyst_Response)

# Crear el objeto WordCloud
wordcloud = WordCloud(width = 800, height = 400, background_color ='white').generate(text)

# Visualizar la nube de palabras
plt.figure(figsize = (8, 8), facecolor = None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad = 0)

# Mostrar la figura
plt.show()