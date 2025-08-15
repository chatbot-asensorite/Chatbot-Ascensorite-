import streamlit as st
import datetime
import re
from typing import Dict

# Configuration de la page
st.set_page_config(
    page_title="🔧 IA Dépannage Ascenseurs",
    page_icon="🏗️",
    layout="wide"
)

# CSS pour le design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .user-message {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #2196f3;
    }
    .bot-message {
        background: #f1f8e9;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

class ElevatorAI:
    def __init__(self):
        self.knowledge = {
            'brands': {
                'otis': {
                    'name': 'Otis',
                    'models': ['GeN2', 'SkyRise', 'SkyBuild'],
                    'codes': {
                        'E1': 'Défaut capteur de porte',
                        'E2': 'Surtemps fermeture porte',
                        'E3': 'Défaut séquence porte',
                        'F1': 'Défaut survitesse',
                        'UC': 'Défaut communication'
                    }
                },
                'kone': {
                    'name': 'Kone',
                    'models': ['MonoSpace', 'EcoSpace', 'MiniSpace'],
                    'codes': {
                        'F7': 'Temps dépassé fermeture porte',
                        'F8': 'Défaut capteur porte',
                        'A1': 'Défaut moteur',
                        'KCE': 'Erreur contrôleur KCE'
                    }
                },
                'schindler': {
                    'name': 'Schindler',
                    'models': ['3300', '5500', '7000'],
                    'codes': {
                        '88': 'Défaut porte',
                        '44': 'Défaut survitesse',
                        '22': 'Défaut alimentation'
                    }
                }
            }
        }
    
    def analyze_message(self, message: str) -> Dict:
        message_lower = message.lower()
        
        # Détection de marque
        detected_brand = None
        for brand_key, brand_info in self.knowledge['brands'].items():
            if brand_key in message_lower:
                detected_brand = brand_key
                break
        
        # Détection de codes d'erreur
        detected_codes = []
        if detected_brand:
            for code in self.knowledge['brands'][detected_brand]['codes'].keys():
                if code.lower() in message_lower:
                    detected_codes.append(code)
        
        return {
            'brand': detected_brand,
            'codes': detected_codes,
            'message': message
        }
    
    def generate_response(self, analysis: Dict) -> str:
        response = "🤖 **Assistant IA Ascenseurs**\n\n"
        
        if analysis['brand']:
            brand_info = self.knowledge['brands'][analysis['brand']]
            response += f"**Marque détectée:** {brand_info['name']}\n"
            response += f"**Modèles:** {', '.join(brand_info['models'])}\n\n"
            
            if analysis['codes']:
                response += "**Codes d'erreur identifiés:**\n"
                for code in analysis['codes']:
                    desc = brand_info['codes'][code]
                    response += f"- `{code}`: {desc}\n"
                response += "\n"
        
        response += """**Solutions recommandées:**
1. Vérifiez l'alimentation générale
2. Contrôlez les capteurs de sécurité
3. Nettoyez les contacts et connexions
4. Testez les systèmes de porte

**⚠️ Sécurité:**
- Toujours couper l'alimentation
- Porter les EPI obligatoires
- Utiliser les dispositifs de consignation

**Besoin d'aide supplémentaire ?** Décrivez plus de détails !"""
        
        return response

def main():
    # En-tête
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Assistant IA - Dépannage Ascenseurs</h1>
        <p>Spécialiste Multi-Marques • Otis • Kone • Schindler</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation
    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = ElevatorAI()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Interface principale
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header("💬 Diagnostic Intelligent")
        
        # Zone de saisie
        user_input = st.text_area(
            "Décrivez votre problème:",
            placeholder="Ex: Ascenseur Otis bloqué, code E1 affiché...",
            height=100
        )
        
        if st.button("🚀 Diagnostic", type="primary"):
            if user_input:
                # Analyse
                analysis = st.session_state.ai_assistant.analyze_message(user_input)
                response = st.session_state.ai_assistant.generate_response(analysis)
                
                # Ajout aux messages
                st.session_state.messages.extend([
                    {
                        'type': 'user',
                        'content': user_input,
                        'timestamp': datetime.datetime.now()
                    },
                    {
                        'type': 'bot',
                        'content': response,
                        'timestamp': datetime.datetime.now()
                    }
                ])
        
        # Affichage des messages
        if st.session_state.messages:
            st.header("📝 Conversation")
            
            for msg in reversed(st.session_state.messages[-6:]):
                if msg['type'] == 'user':
                    st.markdown(f"""
                    <div class="user-message">
                        <strong>👤 Vous ({msg['timestamp'].strftime('%H:%M')}):</strong><br>
                        {msg['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="bot-message">
                        <strong>🤖 Assistant ({msg['timestamp'].strftime('%H:%M')}):</strong><br>
                        {msg['content'].replace('**', '<strong>').replace('**', '</strong>').replace('\\n', '<br>')}
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.header("🏭 Marques")
        
        brands = st.session_state.ai_assistant.knowledge['brands']
        for brand_key, brand_info in brands.items():
            with st.expander(brand_info['name']):
                st.write("**Modèles:**")
                for model in brand_info['models']:
                    st.write(f"• {model}")
        
        st.header("⚡ Exemples")
        examples = [
            "Otis E1 porte bloquée",
            "Kone F7 défaut fermeture",
            "Schindler 88 récurrent"
        ]
        
        for example in examples:
            if st.button(example, key=example):
                st.session_state.example_clicked = example

if __name__ == "__main__":
    main()
