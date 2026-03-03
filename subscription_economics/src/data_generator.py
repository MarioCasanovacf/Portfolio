import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Determinismo
np.random.seed(42)

def generate_saas_hardware_data(output_dir="../data", n_users=5000):
    """
    Genera un modelo relacional simulando un Data Warehouse de una empresa IoT
    con líneas de hardware (Cámaras de Seguridad vs Timbres Inteligentes),
    Logs de Suscripción (SaaS) y Telemetría de uso para análisis de cohortes.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Hardware Sales & Onboarding (A/B Test)
    user_ids = np.arange(10000, 10000 + n_users)
    device_types = np.random.choice(['Security Camera', 'Smart Doorbell'], size=n_users, p=[0.4, 0.6])
    
    # Adquisición distribuida en el último año (Cohortes mensuales)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 12, 31)
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    
    purchase_dates = [start_date + timedelta(days=np.random.randint(0, days_between_dates)) for _ in range(n_users)]
    
    # A/B Testing: Versión Control (Flujo clásico) vs Variante (Flujo optimizado)
    onboarding_version = np.random.choice(['Control', 'Variant'], size=n_users, p=[0.5, 0.5])
    
    users_df = pd.DataFrame({
        'UserID': user_ids,
        'DeviceType': device_types,
        'PurchaseDate': purchase_dates,
        'OnboardingVersion': onboarding_version
    })
    
    users_df['PurchaseDate'] = pd.to_datetime(users_df['PurchaseDate'])
    users_df['CohortMonth'] = users_df['PurchaseDate'].dt.to_period('M').astype(str)
    
    # 2. Subscriptions Fact Table
    # Las cámaras convierten mejor (Attach Rate alto) y el Onboarding Variante también mejora conversión
    subscriptions = []
    
    for _, user in users_df.iterrows():
        base_conv_prob = 0.35 if user['DeviceType'] == 'Security Camera' else 0.20
        # Efecto del A/B Test en Conversión
        if user['OnboardingVersion'] == 'Variant':
            base_conv_prob += 0.15 
            
        converts_to_sub = np.random.rand() < base_conv_prob
        
        if converts_to_sub:
            sub_start = user['PurchaseDate'] + timedelta(days=np.random.randint(1, 14))
            
            # Churn Probability basado en cohorte y dispositivo
            churn_prob = 0.4 if user['DeviceType'] == 'Smart Doorbell' else 0.2
            if user['OnboardingVersion'] == 'Variant':
                churn_prob -= 0.05 # Ligeramente mejor retención con nuevo onboarding
                
            churns = np.random.rand() < churn_prob
            
            if churns:
                # Duración aleatoria antes de churn (1 a 8 meses)
                sub_end = sub_start + timedelta(days=np.random.randint(30, 240))
                is_active = False
            else:
                sub_end = pd.NaT
                is_active = True
                
            subscriptions.append({
                'UserID': user['UserID'],
                'PlanName': 'Premium Cloud Storage',
                'MonthlyFee': 14.99 if user['DeviceType'] == 'Security Camera' else 9.99,
                'SubscriptionStart': sub_start,
                'SubscriptionEnd': sub_end,
                'IsActive': is_active
            })
            
    subs_df = pd.DataFrame(subscriptions)
    
    # 3. Telemetry Logs (DAU/MAU Stickiness)
    # Generaremos logs diarios condensados solo para un mes de muestra (Marzo 2023) 
    # para no saturar memoria, simulando usuarios activos.
    telemetry_records = []
    sample_month_start = datetime(2023, 3, 1)
    
    # Solo usuarios que compraron antes de marzo 2023
    active_users = users_df[users_df['PurchaseDate'] < sample_month_start]
    
    for _, user in active_users.iterrows(): # Usamos un random sample para simular MAU real vs MAU total
        # ¿Entró en el mes?
        if np.random.rand() < 0.8: # 80% MAU
            # ¿Cuántos días activos? (DAU)
            # Cámaras tienen mayor stickiness que Timbres
            mean_days = 20 if user['DeviceType'] == 'Security Camera' else 8
            active_days = np.clip(np.random.normal(mean_days, 5), 1, 31).astype(int)
            
            # Generar logs para esos días
            days_selected = np.random.choice(range(1, 32), size=active_days, replace=False)
            for day in days_selected:
                telemetry_records.append({
                    'UserID': user['UserID'],
                    'LogDate': datetime(2023, 3, day),
                    'AppOpens': np.random.randint(1, 10),
                    'MinutesActive': round(np.random.uniform(2.0, 45.0), 1)
                })
                
    telemetry_df = pd.DataFrame(telemetry_records)
    
    # Exportar a CSV
    users_df.to_csv(os.path.join(output_dir, "hardware_users.csv"), index=False)
    subs_df.to_csv(os.path.join(output_dir, "subscriptions.csv"), index=False)
    telemetry_df.to_csv(os.path.join(output_dir, "telemetry_logs_202303.csv"), index=False)
    
    print(f"[+] DWH Sintético Generado: {len(users_df)} Usuarios, {len(subs_df)} Suscripciones, {len(telemetry_df)} Logs de Telemetría.")
    print(f"    Rutas: {output_dir}/ hardware_users.csv | subscriptions.csv | telemetry_logs.csv")

if __name__ == "__main__":
    print("[*] Generando bases de datos analíticas para Subscription Economics...")
    generate_saas_hardware_data()
