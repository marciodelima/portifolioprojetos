#!/usr/bin/env python
# coding: utf-8

# Demonstracao

# In[1]:

import json
import string
import pandas as pd
import warnings
warnings.filterwarnings("ignore")


# In[31]:


#Parametros Gerais
df_parametros_geral = pd.read_excel('parametros_Gerais.xlsx', sep=",")


# In[138]:


#Parametros - Classe / Empresa
df_parametros = pd.read_excel('parametros_classe.xlsx', sep=",")


# In[5]:


#Load dos modelos - Churn e Sinistro
from sklearn.externals import joblib

modelo_churn = joblib.load('modelos/gbm_modeloChurn.joblib')
modelo_sinistro = joblib.load('modelos/gbm_modeloSinistro.joblib')


# In[57]:


# LOAD Arquivos de Predição
df_full = pd.read_excel('simulador.xlsx')
df_churn = df_full[["cliente","empresa","classeLocalizacao","anosFidelidadeCliente","codigoTipoVeiculo","codigoSucursal","premioLiquidoPagoApolice","valorFranquia","valorPremioFinal","valorDiferencaPremioAnual","valorImportanciaSeguradaCasco","origemProposta","codigoClasseBonus","valorPremioPagoAtual"]]
df_sinistro = df_full[["cliente","empresa","classeLocalizacao","IDHM_R","anosFidelidadeCliente","codigoClasseBonus","codigoClasseLocalizacao","codigoFamiliaVeiculo","codigoMarcaVeiculo","codigoSucursal","codigoTipoVeiculo","diaSemana","diferencaPremioAntNovo","premioLiquidoPagoApolice","valorDiferencaPremioAnual","valorFranquia","valorImportanciaSeguradaCasco","valorPremioFinal","valorPremioPagoAtual"]]


# In[63]:


#Fazendo as previsões
array_churn = df_churn.values
X = array_churn[:,3:14]

array_sinistro = df_sinistro.values
X_sinistro = array_sinistro[:,3:19]


# In[64]:


#Normalizacao e Padronizacao dos dados
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X = scaler.fit_transform(X)
X_sinistro = scaler.fit_transform(X_sinistro)


# In[67]:


Y_churn_prob = modelo_churn.predict_proba(X, num_iteration=modelo_churn.best_iteration_)
Y_sinistro_prob = modelo_sinistro.predict_proba(X_sinistro, num_iteration=modelo_sinistro.best_iteration_)
Y_churn = modelo_churn.predict(X, num_iteration=modelo_churn.best_iteration_)
Y_sinistro = modelo_sinistro.predict(X_sinistro, num_iteration=modelo_sinistro.best_iteration_)


# In[84]:


df_resultado = df_full[["cliente","empresa","classeLocalizacao"]]
df_resultado['Vai_Renovar'] = Y_churn
df_resultado['Ter_Sinistro'] = Y_sinistro
df_resultado['Prob_Nao_Renovacao'] = (Y_churn_prob[:,0] * 100)
df_resultado['Prob_Ter_Sinistro'] = (Y_sinistro_prob[:,1] * 100)

df_resultado['Vai_Renovar'] = ['Sim' if x == 1.0 else  'Nao' for x in df_resultado['Vai_Renovar'] ]
df_resultado['Ter_Sinistro'] = ['Sim' if x == 1.0 else  'Nao' for x in df_resultado['Ter_Sinistro'] ]


# In[175]:


# 100 - Prob_Ter_Sinistro (Percentual de Desconto)
# 35 * (Percentual de Desconto / 100)
# Se abaixo de 10% => Desconto Maximo

# Se Renova Nao e Sinistro Nao - Desconto Maior
# Se Renova Nao e Sinistro Sim - Desconto Menor
# Se Renova Sim e Sinistro Nao - Desconto 0%
# Se Renova Sim e Sinistro Sim - Aumento o preço

desconto_max_Porto = df_parametros_geral.iloc[0,1].astype(float)
desconto_max_Azul = df_parametros_geral.iloc[1,1].astype(float)

lista_classes_Porto = df_parametros[df_parametros.Empresa == 'PORTO'].iloc[:,1:3].values
lista_classes_Azul = df_parametros[df_parametros.Empresa == 'AZUL'].iloc[:,1:3].values

def calcularDesconto(empresa, classe, vaiRenovar, terSinistro, probNaoRenovacao, probTerSinistro): 
    
        desconto_maximo = desconto_max_Porto if (empresa == 'PORTO') else desconto_max_Azul
        if (vaiRenovar == 'Nao'):
            return (desconto_maximo * ((100 - probTerSinistro) / 100) )
        else: 
            return 0.0
            

def calcularAumento(empresa, classe, vaiRenovar, terSinistro, probNaoRenovacao, probTerSinistro): 
        
        aumento_maximo = desconto_max_Porto if (empresa == 'PORTO') else desconto_max_Azul
        if (vaiRenovar == 'Sim'):
            if (terSinistro == 'Sim'): 
                return (aumento_maximo * ( (probTerSinistro - 50.0) / 100 ) )
            else: 
                return 0.0
        else: 
            return 0.0


# In[176]:


df_resultado['desconto'] = [ calcularDesconto(e,c,x,y,z,m) for e,c,x,y,z,m in df_resultado.iloc[:,1:7].values ]
df_resultado['aumento'] = [ calcularAumento(e,c,x,y,z,m) for e,c,x,y,z,m in df_resultado.iloc[:,1:7].values ]


# In[91]:


df_resultado.to_excel('resultado/resultado.xlsx', header=True, index=False, engine='openpyxl')

