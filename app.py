import streamlit as st
import pandas as pd
import json
import datetime
from PIL import Image
import io
import base64
from typing import Dict, List
import sqlite3
import os
import re

# Configuration de la page
st.set_page_config(
    page_title="🔧 IA Dépannage Ascenseurs",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un beau design
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        margin-left: 2rem;
    }
    .bot-message {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: white;
        margin-right: 2rem;
    }
    .brand-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #4facfe;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .error-code {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.5rem;
        border-radius: 8px;
        font-family: monospace;
        font-weight: bold;
    }
    .solution-box {
        background: #f0fdf4;
        border: 2px solid #22c55e;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

class ElevatorAI:
    def __init__(self):
        self.init_database()
        self.load_knowledge_base()
    
    def init_database(self):
        """Initialise la base de données SQLite pour sauvegarder les conversations"""
        try:
            conn = sqlite3.connect('elevator_data.db', check_same_thread=False)
            c = conn.cursor()
            
            # Table des conversations
            c.execute('''CREATE TABLE IF NOT EXISTS conversations
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          timestamp TEXT, 
                          user_message TEXT, 
                          bot_response TEXT, 
                          brand TEXT, 
                          issue_type TEXT,
                          solved BOOLEAN DEFAULT 0)''')
            
            # Table des documents uploadés
            c.execute('''CREATE TABLE IF NOT EXISTS documents
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          filename TEXT, 
                          content TEXT, 
                          brand TEXT, 
                          doc_type TEXT, 
                          upload_date TEXT,
                          processed BOOLEAN DEFAULT 0)''')
            
            # Table des feedbacks utilisateurs
            c.execute('''CREATE TABLE IF NOT EXISTS feedback
                         (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          conversation_id INTEGER, 
                          rating INTEGER, 
                          comment TEXT, 
                          timestamp TEXT)''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            st.error(f"Erreur base de données: {e}")
    
    def load_knowledge_base(self):
        """Base de connaissances complète des ascenseurs"""
        self.knowledge = {
            'brands': {
                'otis': {
                    'name': 'Otis',
                    'models': ['GeN2', 'SkyRise', 'SkyBuild', 'MRL', 'Series 1', 'Compass'],
                    'common_codes': {
                        'E1': 'Défaut capteur de porte - Vérifier photocellules',
                        'E2': 'Surtemps fermeture porte - Nettoyer rails',
                        'E3': 'Défaut séquence porte - Calibrer capteurs',
                        'F1': 'Défaut survitesse - Contrôler régulateur',
                        'F2': 'Défaut frein de sécurité - Test freins obligatoire',
                        'UC': 'Défaut communication - Redémarrer contrôleur',
                        'OL': 'Surcharge - Vérifier cellule de charge',
                        'TS': 'Arrêt étage - Problème capteur niveau'
                    },
                    'diagnostic_steps': {
                        'porte': [
                            'Nettoyer seuils et rails de porte',
                            'Vérifier alignement des capteurs',
                            'Contrôler moteur de porte',
                            'Tester photocellules de sécurité'
                        ],
                        'moteur': [
                            'Vérifier connexions électriques',
                            'Contrôler variateur de fréquence',
                            'Mesurer résistance bobinages',
                            'Tester encoder de position'
                        ]
                    }
                },
                'kone': {
                    'name': 'Kone',
                    'models': ['MonoSpace', 'EcoSpace', 'MiniSpace', 'TranSys', 'MachineRoom-Less'],
                    'common_codes': {
                        'F7': 'Temps dépassé fermeture porte',
                        'F8': 'Défaut capteur porte',
                        'A1': 'Défaut moteur de traction',
                        'A2': 'Défaut système de frein',
                        'KCE': 'Erreur contrôleur KCE',
                        'ECO': 'Défaut système EcoSpace',
                        'COP': 'Erreur boutons cabine'
                    },
                    'diagnostic_steps': {
                        'ecospace': [
                            'Calibrer système EcoSpace',
                            'Vérifier capteurs de présence',
                            'Nettoyer optiques de détection',
                            'Reset paramètres usine'
                        ],
                        'kce': [
                            'Redémarrer contrôleur KCE',
                            'Vérifier connexion Ethernet',
                            'Contrôler alimentation 24V',
                            'Reset configuration réseau'
                        ]
                    }
                },
                'schindler': {
                    'name': 'Schindler',
                    'models': ['3300', '5500', '7000', 'PORT Technology', 'CleanMobility'],
                    'common_codes': {
                        '88': 'Défaut porte principale',
                        '44': 'Défaut survitesse détectée',
                        '22': 'Défaut alimentation système',
                        'PORT': 'Erreur système PORT',
                        '33': 'Problème communication',
                        '77': 'Défaut frein de sécurité'
                    },
                    'diagnostic_steps': {
                        'port': [
                            'Redémarrer système PORT',
                            'Vérifier connexions réseau',
                            'Contrôler serveur principal',
                            'Reset base de données'
                        ]
                    }
                },
                'thyssenkrupp': {
                    'name': 'ThyssenKrupp',
                    'models': ['Evolution', 'Synergy', 'Essence', 'TWIN', 'MULTI'],
                    'common_codes': {
                        'Dr1': 'Défaut porte cabine',
                        'Dr2': 'Défaut porte palière',
                        'Sp1': 'Survitesse détectée',
                        'Br1': 'Défaut frein électrique',
                        'Mo1': 'Défaut moteur traction'
                    }
                },
                'mitsubishi': {
                    'name': 'Mitsubishi',
                    'models': ['ELENESSA', 'NEXIEZ', 'GPS-III'],
                    'common_codes': {
                        'Er1': 'Erreur capteur porte',
                        'Er2': 'Problème communication',
                        'Er3': 'Défaut alimentation'
                    }
                }
            },
            'general_safety': [
                "🔴 TOUJOURS couper l'alimentation avant intervention",
                "🦺 Porter les EPI obligatoires (casque, chaussures sécurité)",
                "🔒 Utiliser les dispositifs de consignation",
                "⚠️ Vérifier tous les arrêts d'urgence",
                "📞 Prévenir la maintenance avant intervention",
                "📋 Documenter toute intervention"
            ]
        }
    
    def analyze_message(self, message: str) -> Dict:
        """Analyse intelligente du message utilisateur"""
        message_lower = message.lower()
        
        # Détection de marque avec synonymes
        brand_synonyms = {
            'otis': ['otis', 'gen2', 'skyrise'],
            'kone': ['kone', 'monospace', 'ecospace', 'minispace'],
            'schindler': ['schindler', '3300', '5500', '7000', 'port'],
            'thyssenkrupp': ['thyssenkrupp', 'thyssen', 'tk', 'evolution', 'synergy'],
            'mitsubishi': ['mitsubishi', 'elenessa', 'nexiez']
        }
        
        detected_brand = None
        for brand_key, synonyms in brand_synonyms.items():
            if any(syn in message_lower for syn in synonyms):
                detected_brand = brand_key
                break
        
        # Détection de codes d'erreur avec regex
        detected_codes = []
        error_patterns = [
            r'\b[A-Z]\d+\b',  # F1, E2, etc.
            r'\b\d{1,3}\b',   # 88, 44, etc.
            r'\b[A-Z]{2,4}\b' # UC, KCE, PORT, etc.
        ]
        
        for pattern in error_patterns:
            matches = re.findall(pattern, message.upper())
            detected_codes.extend(matches)
        
        # Validation des codes selon la marque
        valid_codes = []
        if detected_brand and detected_brand in self.knowledge['brands']:
            brand_codes = self.knowledge['brands'][detected_brand]['common_codes']
            for code in detected_codes:
                if code in brand_codes:
                    valid_codes.append(code)
        
        # Détection de problèmes par mots-clés
        issue_keywords = {
            'porte': ['porte', 'door', 'fermeture', 'ouverture', 'photocellule', 'capteur'],
            'moteur': ['moteur', 'motor', 'vitesse', 'speed', 'traction', 'rotation'],
            'frein': ['frein', 'brake', 'arrêt', 'blocage', 'sécurité'],
            'communication': ['communication', 'réseau', 'can', 'ethernet', 'connexion'],
            'nivellement': ['niveau', 'nivellement', 'alignement', 'position'],
            'surcharge': ['surcharge', 'poids', 'charge', 'capacité'],
            'survitesse': ['survitesse', 'vitesse', 'régulateur', 'limiteur']
        }
        
        detected_issues = []
        for issue_type, keywords in issue_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_issues.append(issue_type)
        
        # Analyse de sentiment (urgence)
        urgency_keywords = ['urgent', 'bloqué', 'panne', 'arrêt', 'coincé', 'danger']
        is_urgent = any(keyword in message_lower for keyword in urgency_keywords)
        
        return {
            'brand': detected_brand,
            'codes': valid_codes,
            'issues': detected_issues,
            'is_urgent': is_urgent,
            'message': message
        }
    
    def generate_response(self, analysis: Dict) -> str:
        """Génère une réponse détaillée et personnalisée"""
        response = ""
        
        # En-tête avec urgence
        if analysis['is_urgent']:
            response += "🚨 **INTERVENTION URGENTE DÉTECTÉE** 🚨\n\n"
        
        response += "🤖 **Assistant IA Spécialisé Ascenseurs**\n\n"
        
        # Informations sur la marque
        if analysis['brand']:
            brand_info = self.knowledge['brands'][analysis['brand']]
            response += f"**🏭 Marque identifiée:** {brand_info['name']}\n"
            response += f"**📋 Modèles compatibles:** {', '.join(brand_info['models'][:3])}...\n\n"
            
            # Codes d'erreur avec solutions
            if analysis['codes']:
                response += "**🔍 CODES D'ERREUR ANALYSÉS:**\n"
                for code in analysis['codes']:
                    if code in brand_info['common_codes']:
                        description = brand_info['common_codes'][code]
                        response += f"```\n🚨 {code}: {description}\n```\n"
                response += "\n"
        
        # Solutions par type de problème
        if analysis['issues']:
            response += "**🔧 SOLUTIONS RECOMMANDÉES:**\n\n"
            
            for issue in analysis['issues']:
                response += f"**➤ Problème {issue.upper()}:**\n"
                
                if analysis['brand'] and issue in self.knowledge['brands'][analysis['brand']].get('diagnostic_steps', {}):
                    steps = self.knowledge['brands'][analysis['brand']]['diagnostic_steps'][issue]
                    for i, step in enumerate(steps, 1):
                        response += f"   {i}. {step}\n"
                else:
                    # Solutions génériques
                    generic_solutions = {
                        'porte': ['Nettoyer rails et seuils', 'Vérifier capteurs', 'Contrôler moteur porte'],
                        'moteur': ['Vérifier connexions', 'Contrôler alimentation', 'Mesurer résistances'],
                        'communication': ['Redémarrer système', 'Vérifier câblage', 'Reset paramètres']
                    }
                    if issue in generic_solutions:
                        for i, step in enumerate(generic_solutions[issue], 1):
                            response += f"   {i}. {step}\n"
                
                response += "\n"
        
        # Procédures de sécurité
        response += "**⚠️ SÉCURITÉ OBLIGATOIRE:**\n"
        for safety_rule in self.knowledge['general_safety'][:4]:
            response += f"• {safety_rule}\n"
        
        # Contact support
        if analysis['brand']:
            response += f"\n**📞 Support {self.knowledge['brands'][analysis['brand']]['name']}:** Contactez le service technique officiel en cas de doute\n"
        
        response += "\n**💡 Besoin d'aide supplémentaire ?** Uploadez une photo du problème ou des schémas techniques !"
        
        return response
    
    def save_conversation(self, user_msg: str, bot_response: str, analysis: Dict):
        """Sauvegarde intelligente des conversations"""
        try:
            conn = sqlite3.connect('elevator_data.db', check_same_thread=False)
            c = conn.cursor()
            
            timestamp = datetime.datetime.now().isoformat()
            brand = analysis.get('brand', 'unknown')
            issue_type = ','.join(analysis.get('issues', []))
            
            c.execute("""INSERT INTO conversations 
                         (timestamp, user_message, bot_response, brand, issue_type) 
                         VALUES (?, ?, ?, ?, ?)""", 
                      (timestamp, user_msg, bot_response, brand, issue_type))
            
            conn.commit()
            conn.close()
            
            # Mise à jour des statistiques en session
            if 'stats' not in st.session_state:
                st.session_state.stats = {'total': 0, 'brands': {}}
            
            st.session_state.stats['total'] += 1
            if brand != 'unknown':
                st.session_state.stats['brands'][brand] = st.session_state.stats['brands'].get(brand, 0) + 1
                
        except Exception as e:
            st.error(f"Erreur sauvegarde: {e}")

def get_stats():
    """Récupère les statistiques d'utilisation"""
    try:
        conn = sqlite3.connect('elevator_data.db', check_same_thread=False)
        c = conn.cursor()
        
        # Total consultations
        c.execute("SELECT COUNT(*) FROM conversations")
        total = c.fetchone()[0]
        
        # Par marque
        c.execute("SELECT brand, COUNT(*) FROM conversations WHERE brand != 'unknown' GROUP BY brand")
        brands_data = c.fetchall()
        
        # Problèmes fréquents
        c.execute("SELECT issue_type, COUNT(*) FROM conversations WHERE issue_type != '' GROUP BY issue_type ORDER BY COUNT(*) DESC LIMIT 5")
        issues_data = c.fetchall()
        
        conn.close()
        
        return {
            'total': total,
            'brands': dict(brands_data),
            'issues': dict(issues_data)
        }
    except:
        return {'total': 0, 'brands': {}, 'issues': {}}

# Interface Streamlit principale
def main():
    # En-tête attractif
    st.markdown("""
    <div class="main-header">
        <h1>🔧 Assistant IA - Dépannage Ascenseurs</h1>
        <h3>Spécialiste Multi-Marques • Diagnostic Intelligent • Solutions Rapides</h3>
        <p>Otis • Kone • Schindler • ThyssenKrupp • Mitsubishi • Et plus encore...</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation de l'IA
    if 'ai_assistant' not in st.session_state:
        st.session_state.ai_assistant = ElevatorAI()
        st.success("🚀 IA initialisée avec succès !")
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Layout principal en colonnes
    col_main, col_sidebar = st.columns([3, 1])
    
    # Interface de chat principal
    with col_main:
        st.header("💬 Diagnostic Intelligent")
        
        # Zone de saisie améliorée
        st.markdown("**Décrivez votre problème d'ascenseur :**")
        user_input = st.text_area(
            "",
            placeholder="Ex: Ascenseur Otis GeN2 bloqué au 3ème étage, code erreur E1 affiché, portes ne se ferment plus...",
            height=120,
            help="Plus vous donnez de détails, meilleur sera le diagnostic !"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            send_button = st.button("🚀 Diagnostic", type="primary")
        
        with col2:
            clear_button = st.button("🗑️ Effacer")
        
        # Upload de fichiers
        st.markdown("**📎 Ajouter des documents (optionnel) :**")
        uploaded_files = st.file_uploader(
            "",
            type=['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'],
            accept_multiple_files=True,
            help="Schémas techniques, photos du problème, manuels..."
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} fichier(s) prêt(s) à analyser")
        
        # Traitement du message
        if send_button and user_input:
            with st.spinner("🧠 Analyse en cours..."):
                # Analyse
                analysis = st.session_state.ai_assistant.analyze_message(user_input)
                response = st.session_state.ai_assistant.generate_response(analysis)
                
                # Sauvegarde
                st.session_state.ai_assistant.save_conversation(user_input, response, analysis)
                
                # Ajout à l'historique
                st.session_state.messages.extend([
                    {
                        'type': 'user',
                        'conte
