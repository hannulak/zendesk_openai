import streamlit as st
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Simula la carga de un DataFrame
# Asegúrate de reemplazar esto con la carga de tu propio DataFrame
data = {
    'text': ['hello world', 'streamlit is awesome', 'word cloud from streamlit']
}
df = pd.DataFrame(data)

def plot_word_cloud():
    text = ' '.join(df['text'])  # Combina todo el texto del DataFrame
    wordcloud = WordCloud(width=800, height=400).generate(text)

    # Configurar la visualización usando matplotlib
    plt.figure(figsize=(10, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.show()

# Streamlit app
def main():
    st.title('Word Cloud Visualization')
    st.write("This is a simple word cloud visualization.")

    if st.button('Show Word Cloud'):
        st.set_option('deprecation.showPyplotGlobalUse', False)  # Opción para evitar una advertencia en Streamlit
        plot_word_cloud()
        st.pyplot()  # Mostrar la figura en la interfaz de Streamlit

if __name__ == '__main__':
    main()

