"""Selfie phenotype check — HIrisPlex-S SNP prediction + MediaPipe face mesh comparison."""

import io

import numpy as np
import pandas as pd

# HIrisPlex-S SNPs for phenotype prediction
EYE_COLOR_SNPS = {
    "rs12913832": {  # HERC2 — strongest eye color predictor
        "GG": "blue", "AG": "green_hazel", "GA": "green_hazel", "AA": "brown",
    },
    "rs1800407": {  # OCA2
        "CC": "blue_shift", "CT": "neutral", "TC": "neutral", "TT": "brown_shift",
    },
    "rs12896399": {  # SLC24A4
        "GG": "blue_shift", "GT": "neutral", "TG": "neutral", "TT": "brown_shift",
    },
}

HAIR_COLOR_SNPS = {
    "rs1805007": {  # MC1R — red hair
        "CC": "not_red", "CT": "red_carrier", "TC": "red_carrier", "TT": "red",
    },
    "rs1805008": {  # MC1R — red hair variant 2
        "CC": "not_red", "CT": "red_carrier", "TC": "red_carrier", "TT": "red",
    },
    "rs1015362": {  # ASIP
        "CC": "darker", "CA": "medium", "AC": "medium", "AA": "lighter",
    },
}

SKIN_SNPS = {
    "rs1426654": {  # SLC24A5 — light skin in Europeans
        "AA": "lighter", "AG": "medium", "GA": "medium", "GG": "darker",
    },
    "rs16891982": {  # SLC45A2
        "CC": "lighter", "CG": "medium", "GC": "medium", "GG": "darker",
    },
}


def _predict_from_snps(snps: pd.DataFrame) -> dict:
    """Predict phenotype from HIrisPlex-S SNPs."""
    lookup = dict(zip(snps["rsid"].str.lower(), snps["genotype"]))

    # Eye color
    herc2 = lookup.get("rs12913832", "")
    eye_pred = EYE_COLOR_SNPS.get("rs12913832", {}).get(herc2.upper(), "unknown")
    eye_map = {"blue": "Blue", "green_hazel": "Green/Hazel", "brown": "Brown", "unknown": "Unknown"}
    eye_color = eye_map.get(eye_pred, "Unknown")

    # Hair color
    mc1r_1 = lookup.get("rs1805007", "")
    mc1r_2 = lookup.get("rs1805008", "")
    asip = lookup.get("rs1015362", "")

    mc1r_1_call = HAIR_COLOR_SNPS.get("rs1805007", {}).get(mc1r_1.upper(), "not_red")
    mc1r_2_call = HAIR_COLOR_SNPS.get("rs1805008", {}).get(mc1r_2.upper(), "not_red")

    if mc1r_1_call == "red" or mc1r_2_call == "red":
        hair_color = "Red"
    elif mc1r_1_call == "red_carrier" or mc1r_2_call == "red_carrier":
        asip_call = HAIR_COLOR_SNPS.get("rs1015362", {}).get(asip.upper(), "medium")
        hair_color = "Auburn/Reddish" if asip_call == "lighter" else "Brown"
    else:
        asip_call = HAIR_COLOR_SNPS.get("rs1015362", {}).get(asip.upper(), "medium")
        hair_map = {"darker": "Black/Dark Brown", "medium": "Brown", "lighter": "Light Brown/Blonde"}
        hair_color = hair_map.get(asip_call, "Brown")

    # Skin tone (Fitzpatrick scale approximation)
    slc24a5 = lookup.get("rs1426654", "")
    slc45a2 = lookup.get("rs16891982", "")
    skin_scores = []
    s1 = SKIN_SNPS.get("rs1426654", {}).get(slc24a5.upper(), "medium")
    s2 = SKIN_SNPS.get("rs16891982", {}).get(slc45a2.upper(), "medium")
    score_map = {"lighter": 1, "medium": 3, "darker": 5}
    avg = (score_map.get(s1, 3) + score_map.get(s2, 3)) / 2
    fitzpatrick = max(1, min(6, round(avg)))
    fitz_labels = {1: "I (Very Fair)", 2: "II (Fair)", 3: "III (Medium)", 4: "IV (Olive)", 5: "V (Brown)", 6: "VI (Dark)"}
    skin_tone = fitz_labels.get(fitzpatrick, "III (Medium)")

    return {
        "eye_color": eye_color,
        "hair_color": hair_color,
        "skin_tone": skin_tone,
        "fitzpatrick": fitzpatrick,
        "snps_used": {
            "eye": {"rs12913832": herc2, "rs1800407": lookup.get("rs1800407", "N/A"), "rs12896399": lookup.get("rs12896399", "N/A")},
            "hair": {"rs1805007": mc1r_1, "rs1805008": mc1r_2, "rs1015362": asip},
            "skin": {"rs1426654": slc24a5, "rs16891982": slc45a2},
        },
    }


def _analyze_face(img_bytes: bytes) -> dict:
    """Run MediaPipe face mesh on selfie and extract phenotype signals."""
    try:
        import mediapipe as mp
        from PIL import Image

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_array = np.array(img)

        face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=True, max_num_faces=1, min_detection_confidence=0.5
        )
        results = face_mesh.process(img_array)
        face_mesh.close()

        if not results.multi_face_landmarks:
            return {"detected": False, "error": "No face detected in image"}

        landmarks = results.multi_face_landmarks[0]
        h, w = img_array.shape[:2]

        # Sample iris region for eye color (landmarks 468-477 are iris in face mesh)
        # Use landmarks around the eye instead for broader compatibility
        left_eye_indices = [33, 133, 159, 145]
        eye_pixels = []
        for idx in left_eye_indices:
            lm = landmarks.landmark[idx]
            x, y = int(lm.x * w), int(lm.y * h)
            if 0 <= x < w and 0 <= y < h:
                eye_pixels.append(img_array[y, x])

        # Sample cheek for skin tone
        cheek_indices = [234, 454]  # left and right cheek
        skin_pixels = []
        for idx in cheek_indices:
            lm = landmarks.landmark[idx]
            x, y = int(lm.x * w), int(lm.y * h)
            if 0 <= x < w and 0 <= y < h:
                skin_pixels.append(img_array[y, x])

        # Rough color analysis
        eye_color_obs = "unknown"
        if eye_pixels:
            avg_eye = np.mean(eye_pixels, axis=0)
            r, g, b = avg_eye
            if b > r and b > g:
                eye_color_obs = "Blue"
            elif g > r and g > b:
                eye_color_obs = "Green/Hazel"
            else:
                eye_color_obs = "Brown"

        skin_lightness = "medium"
        if skin_pixels:
            avg_skin = np.mean(skin_pixels, axis=0)
            luminance = 0.299 * avg_skin[0] + 0.587 * avg_skin[1] + 0.114 * avg_skin[2]
            if luminance > 180:
                skin_lightness = "fair"
            elif luminance > 120:
                skin_lightness = "medium"
            else:
                skin_lightness = "dark"

        return {
            "detected": True,
            "observed_eye_color": eye_color_obs,
            "observed_skin_lightness": skin_lightness,
        }

    except Exception as e:
        return {"detected": False, "error": str(e)}


def analyze_selfie(img_bytes: bytes, snps: pd.DataFrame, ancestry: dict) -> dict:
    """Full selfie analysis: genetic prediction + face mesh observation."""
    prediction = _predict_from_snps(snps)
    observation = _analyze_face(img_bytes)

    # Match scoring
    matches = {}
    if observation.get("detected"):
        matches["eye_color"] = prediction["eye_color"].lower() == observation["observed_eye_color"].lower()
        matches["skin_tone"] = (
            (prediction["fitzpatrick"] <= 2 and observation["observed_skin_lightness"] == "fair")
            or (prediction["fitzpatrick"] in (3, 4) and observation["observed_skin_lightness"] == "medium")
            or (prediction["fitzpatrick"] >= 5 and observation["observed_skin_lightness"] == "dark")
        )
        match_count = sum(matches.values())
        confidence = round(match_count / len(matches) * 100)
    else:
        confidence = None

    # Equity note
    is_non_european = ancestry and ancestry.get("European", 100) < 50
    equity_note = None
    if is_non_european:
        equity_note = (
            "Phenotype prediction models were primarily trained on European populations "
            "- this affects accuracy for your ancestry group. This is the same bias "
            "G-Nome corrects in your clinical risk scores."
        )

    return {
        "genetic_prediction": prediction,
        "selfie_observation": observation,
        "matches": matches,
        "confidence_pct": confidence,
        "equity_note": equity_note,
        "disclaimer": "Phenotype prediction is probabilistic and based on a small number of SNPs. Actual appearance is influenced by many additional genetic and environmental factors.",
    }
