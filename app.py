from pydantic import BaseModel, Field
from google import genai
from PIL import Image
import streamlit as st

MODEL = 'gemini-3.1-flash-lite' # JAMAIS ALTERAR ESSE MODELO, PODE CAUSAR ERROS


class Refeicao(BaseModel):
    nome: str = Field(description="Nome do prato identificado na foto.")
    calorias: int = Field(description="Estimativa de calorias totais para a porção mostrada.")
    proteinas: float = Field(description="Quantidade estimada de proteínas em gramas.")
    carboidratos: float = Field(description="Quantidade estimada de carboidratos em gramas.")
    gorduras: float = Field(description="Quantidade estimada de gorduras em gramas.")
    vegetariano: bool = Field(description="Se o prato é adequado para vegetarianos.")
    vegano: bool = Field(description="Se o prato é adequado para veganos.")
    gluten_free: bool = Field(description="Se o prato é livre de glúten.")
    alergicos: list[str] = Field(description="Lista de alérgenos comuns no prato.")
    tipo_cozinha: str = Field(description="Tipo de culinária do prato.")
    score_saude: int = Field(description="Score de saúde do prato de 1 a 10.")
    nota_confianca: int = Field(description="Nota de confiança de 1 até 5 sobre a certeza na identificação do prato.")


# --- Chamada à API Gemini ---

# Inicializa o cliente Gemini usando as credenciais do Streamlit Secrets
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
except Exception as e:
    st.error(f"Erro ao inicializar o cliente Gemini. Certifique-se de que a chave API está configurada em .streamlit/secrets.toml. Detalhes: {e}")
    client = None

# CSS personalizado e Branding para layout Premium
st.markdown("""
    <div style="text-align: center; padding: 1.5rem; margin-bottom: 2rem; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; border: 1px solid #334155;">
        <h1 style="color: #f8fafc; font-family: 'Inter', sans-serif; font-size: 2.8rem; margin: 0; font-weight: 800;">🥗 NutriPedro <span style="background: linear-gradient(90deg, #38bdf8 0%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">AI</span></h1>
        <p style="color: #94a3b8; font-size: 1.1rem; margin-top: 0.5rem; margin-bottom: 0;">Análise nutricional instantânea e inteligente baseada em imagens</p>
    </div>
    
    <style>
        .diet-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.85rem;
            margin-right: 8px;
            margin-bottom: 8px;
            text-align: center;
        }
        .badge-true {
            background-color: rgba(52, 211, 153, 0.15);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.3);
        }
        .badge-false {
            background-color: rgba(248, 113, 113, 0.15);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.3);
        }
        .allergen-pill {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            background-color: rgba(251, 191, 36, 0.15);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.3);
            font-weight: 600;
            font-size: 0.85rem;
            margin-right: 8px;
            margin-bottom: 8px;
        }
    </style>
""", unsafe_allow_html=True)

# Cache do resultado da API para evitar chamadas duplicadas ao re-renderizar a página
@st.cache_data(show_spinner=False)
def analisar_imagem(image_bytes):
    if client is None:
        return None
    try:
        import io
        img = Image.open(io.BytesIO(image_bytes))
        resposta = client.models.generate_content(
            model=MODEL,
            contents=[
                "Analise esta imagem de refeição e extraia os dados nutricionais solicitados.",
                img,
            ],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Refeicao.model_json_schema(),
            ),
        )
        return resposta.text
    except Exception as e:
        return f"ERROR: {str(e)}"

# Layout de duas colunas principais
col_upload, col_result = st.columns([1, 2], gap="large")

with col_upload:
    st.subheader("📷 Entrada da Imagem")
    tab_camera, tab_upload = st.tabs(["🎥 Capturar da Câmera", "📁 Upload de Arquivo"])
    
    uploaded_file = None
    
    with tab_camera:
        camera_file = st.camera_input("Tire uma foto do seu prato")
        if camera_file is not None:
            uploaded_file = camera_file
            
    with tab_upload:
        file_upload = st.file_uploader(
            "Selecione uma imagem para análise",
            type=["jpg", "png", "webp"],
            help="Suba uma foto nítida do seu prato para obter as informações nutricionais completas."
        )
        if file_upload is not None:
            uploaded_file = file_upload
            st.image(uploaded_file, caption="Imagem carregada com sucesso", use_container_width=True)

with col_result:
    if uploaded_file is not None:
        st.subheader("✨ Resultado da Análise")
        
        with st.spinner("Analisando refeição com Gemini AI... 🤖"):
            image_bytes = uploaded_file.getvalue()
            resposta_text = analisar_imagem(image_bytes)
            
        if resposta_text:
            if resposta_text.startswith("ERROR:"):
                st.error(f"Erro na análise do Gemini: {resposta_text[6:]}")
            else:
                try:
                    dados_refeicao = Refeicao.model_validate_json(resposta_text)
                    
                    # Apresenta os dados
                    st.markdown(f"### 🍽️ {dados_refeicao.nome}")
                    st.caption(f"**Culinária/Estilo:** {dados_refeicao.tipo_cozinha}")
                    st.write("---")
                    
                    # Métricas de Macronutrientes e Saúde
                    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                    with m_col1:
                        st.metric(label="🔥 Calorias", value=f"{dados_refeicao.calorias} kcal")
                    with m_col2:
                        st.metric(label="💪 Proteínas", value=f"{dados_refeicao.proteinas}g")
                    with m_col3:
                        st.metric(label="🍞 Carbos", value=f"{dados_refeicao.carboidratos}g")
                    with m_col4:
                        st.metric(label="🥑 Gorduras", value=f"{dados_refeicao.gorduras}g")
                    with m_col5:
                        st.metric(label="🥗 Score Saúde", value=f"{dados_refeicao.score_saude}/10")
                    
                    st.write("---")
                    
                    # Detalhes e Alérgenos
                    det_col1, det_col2 = st.columns(2)
                    
                    with det_col1:
                        st.markdown("#### 🥦 Preferências Alimentares")
                        
                        veg_badge = "badge-true" if dados_refeicao.vegetariano else "badge-false"
                        veg_lbl = "Vegetariano" if dados_refeicao.vegetariano else "Não Vegetariano"
                        
                        vegan_badge = "badge-true" if dados_refeicao.vegano else "badge-false"
                        vegan_lbl = "Vegano" if dados_refeicao.vegano else "Não Vegano"
                        
                        gf_badge = "badge-true" if dados_refeicao.gluten_free else "badge-false"
                        gf_lbl = "Sem Glúten" if dados_refeicao.gluten_free else "Contém Glúten"
                        
                        st.markdown(f"""
                        <div style="margin-top: 10px;">
                            <span class="diet-badge {veg_badge}">{veg_lbl}</span>
                            <span class="diet-badge {vegan_badge}">{vegan_lbl}</span>
                            <span class="diet-badge {gf_badge}">{gf_lbl}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with det_col2:
                        st.markdown("#### ⚠️ Alérgenos")
                        if dados_refeicao.alergicos:
                            badges = "".join([f'<span class="allergen-pill">{a}</span>' for a in dados_refeicao.alergicos])
                            st.markdown(f'<div style="margin-top: 10px;">{badges}</div>', unsafe_allow_html=True)
                        else:
                            st.success("Nenhum alérgeno comum detectado!")
                            
                except Exception as ex:
                    st.error(f"Erro ao processar os dados de resposta: {ex}")
                    st.code(resposta_text)
    else:
        # Estado Inicial
        st.info("👋 Por favor, envie uma foto na seção ao lado para iniciar a análise nutricional automática!")
        
        st.markdown("""
            <div style="background: rgba(30, 41, 59, 0.4); border: 1px dashed #334155; border-radius: 12px; padding: 1.5rem; margin-top: 1.5rem;">
                <h4 style="margin-top: 0; color: #38bdf8; font-family: 'Inter', sans-serif;">Como funciona:</h4>
                <ol style="color: #94a3b8; padding-left: 1.2rem; margin-bottom: 0; font-size: 0.95rem; line-height: 1.6;">
                    <li>Você carrega uma foto do seu prato (.jpg, .png ou .webp).</li>
                    <li>O modelo de IA <strong>gemini-3.1-flash-lite</strong> realiza a análise visual.</li>
                    <li>As informações são extraídas de forma estruturada baseada no schema técnico.</li>
                    <li>Macronutrientes estimativos, preferências e alérgenos são exibidos na tela com exclusão da nota de confiança interna.</li>
                </ol>
            </div>
        """, unsafe_allow_html=True)
