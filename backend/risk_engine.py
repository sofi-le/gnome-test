import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# --- 1. Data Generation ---
def generate_mock_data():
    """
    Programmatically creates a Pandas DataFrame with 500 rows of synthetic genomic data.
    Features: rs1001 through rs1050, ancestry_group.
    Targets: high_risk_cad, high_risk_t2d, high_risk_bc.
    """
    np.random.seed(42)
    n_samples = 500
    
    # Generate 50 SNP columns (rs1001 to rs1050) with values 0, 1, or 2
    snp_columns = [f'rs{i}' for i in range(1001, 1051)]
    snps_data = np.random.choice([0, 1, 2], size=(n_samples, 50), p=[0.6, 0.3, 0.1])
    
    # Generate ancestry_group (0=EUR, 1=AFR, 2=AMR, 3=EAS, 4=SAS, 5=MID)
    ancestry_group = np.random.randint(0, 6, size=(n_samples, 1))
    
    # Combine into DataFrame
    df = pd.DataFrame(snps_data, columns=snp_columns)
    df['ancestry_group'] = ancestry_group
    
    # CAD Synthetic bias: rs1010, rs1020
    logit_cad = -2.0 + 1.2 * df['rs1010'] + 0.8 * df['rs1020']
    ancestry_effects_cad = {0: 0.0, 1: 0.2, 2: 0.1, 3: -0.5, 4: 1.0, 5: 0.3}
    logit_cad += df['ancestry_group'].map(ancestry_effects_cad) + np.random.normal(0, 0.5, n_samples)
    df['high_risk_cad'] = (1 / (1 + np.exp(-logit_cad)) > 0.5).astype(int)

    # T2D Synthetic bias: rs1030, rs1040
    logit_t2d = -1.5 + 1.5 * df['rs1030'] + 1.0 * df['rs1040']
    ancestry_effects_t2d = {0: 0.1, 1: 0.8, 2: 0.5, 3: 0.2, 4: 0.6, 5: 0.4}
    logit_t2d += df['ancestry_group'].map(ancestry_effects_t2d) + np.random.normal(0, 0.5, n_samples)
    df['high_risk_t2d'] = (1 / (1 + np.exp(-logit_t2d)) > 0.5).astype(int)

    # Breast Cancer Synthetic bias: rs1005, rs1015
    logit_bc = -2.5 + 2.0 * df['rs1005'] + 1.2 * df['rs1015']
    ancestry_effects_bc = {0: 0.3, 1: 0.1, 2: 0.0, 3: 0.2, 4: 0.1, 5: 0.1}
    logit_bc += df['ancestry_group'].map(ancestry_effects_bc) + np.random.normal(0, 0.5, n_samples)
    df['high_risk_bc'] = (1 / (1 + np.exp(-logit_bc)) > 0.5).astype(int)
    
    return df

# --- 2. Model Training ---
def train_all_models(df):
    """
    Trains an Elastic Net Logistic Regression model for each disease.
    """
    targets = {
        "Coronary Artery Disease": "high_risk_cad",
        "Type 2 Diabetes": "high_risk_t2d",
        "Breast Cancer": "high_risk_bc"
    }
    
    X = df.drop(columns=list(targets.values()))
    feature_names = list(X.columns)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    models = {}
    for disease_name, target_col in targets.items():
        y = df[target_col]
        model = LogisticRegression(
            penalty='elasticnet', solver='saga', l1_ratio=0.5, max_iter=1000, random_state=42
        )
        model.fit(X_scaled, y)
        models[disease_name] = model
        
    return models, scaler, feature_names

# --- Global Initialization ---
_df = generate_mock_data()
_models, _scaler, _feature_names = train_all_models(_df)

# --- 3. Live Inference Function ---
def predict_user_risk(user_snps: dict, ancestry_group: int) -> dict:
    """
    Predicts the risk probability and identifies the top 3 driving factors for all diseases.
    Returns: {"Disease Name": {"risk_probability": float, "driving_factors": list}, ...}
    """
    input_data = []
    for feature in _feature_names:
        if feature == 'ancestry_group':
            input_data.append(ancestry_group)
        else:
            input_data.append(user_snps.get(feature, 0))
    
    X_input = np.array(input_data).reshape(1, -1)
    X_scaled = _scaler.transform(X_input)
    
    results = {}
    for disease_name, model in _models.items():
        risk_prob = model.predict_proba(X_scaled)[0][1]
        
        coefficients = model.coef_[0]
        impact_scores = coefficients * X_scaled[0]
        
        feature_impacts = list(zip(_feature_names, impact_scores))
        feature_impacts.sort(key=lambda x: x[1], reverse=True)
        top_3_drivers = [feat for feat, impact in feature_impacts[:3]]
        
        results[disease_name] = {
            "risk_probability": round(float(risk_prob), 4),
            "driving_factors": top_3_drivers
        }
        
    return results

# --- Quick Test Block ---
if __name__ == "__main__":
    fake_user_snps = {'rs1010': 2, 'rs1030': 1, 'rs1005': 2}
    fake_ancestry = 4
    results = predict_user_risk(fake_user_snps, fake_ancestry)
    for disease, data in results.items():
        print(f"{disease} Risk: {data['risk_probability'] * 100:.1f}% | Drivers: {data['driving_factors']}")
