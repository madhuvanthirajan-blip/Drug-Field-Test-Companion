import cv2
import numpy as np

def sample_region(image, x1, y1, x2, y2):
    h, w = image.shape[:2]
    x1, x2 = max(0, int(x1*w)), min(w, int(x2*w))
    y1, y2 = max(0, int(y1*h)), min(h, int(y2*h))
    crop = image[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    bgr = crop.mean(axis=(0,1))
    hm = hsv.mean(axis=(0,1))
    return {
        "b": float(bgr[0]), "g": float(bgr[1]), "r": float(bgr[2]),
        "h": float(hm[0]), "s": float(hm[1]), "v": float(hm[2])
    }

def analyze_image(image_bgr):
    # Guided prototype layout: reference card left, test area right.
    card = sample_region(image_bgr, .05, .35, .48, .75)
    sample = sample_region(image_bgr, .55, .30, .95, .80)
    if sample is None:
        raise ValueError("Could not sample test region.")

    card_v = card["v"] if card else 128.0
    light_factor = float(np.clip(128.0 / max(card_v, 30.0), .65, 1.45))
    r = np.clip(sample["r"] * light_factor, 0, 255)
    g = np.clip(sample["g"] * light_factor, 0, 255)
    b = np.clip(sample["b"] * light_factor, 0, 255)

    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0,0]
    hue, sat, val = map(float, hsv)

    blue_score = max(0.0, 1.0 - min(abs(hue - 100.0)/45.0, 1.0))
    cyan_score = max(0.0, 1.0 - min(abs(hue - 90.0)/40.0, 1.0))
    positive_score = 100 * (0.65 * max(blue_score, cyan_score) + 0.35 * min(sat/150, 1))
    neutral_score = 100 * max(0.0, 1.0 - sat/90)

    if positive_score >= 68:
        result = "POSITIVE"
        confidence = min(96.0, max(68.0, positive_score))
        explanation = "The calibrated sample is strongly blue/cyan and matches the prototype positive colour family."
    elif neutral_score >= 62:
        result = "NEGATIVE"
        confidence = min(94.0, max(62.0, neutral_score))
        explanation = "The calibrated sample is comparatively neutral/low-saturation and matches the prototype negative family."
    else:
        result = "INCONCLUSIVE"
        confidence = max(50.0, min(66.0, 100.0 - abs(positive_score-neutral_score)))
        explanation = "The measured colour does not clearly match either prototype reference family."

    h, w = image_bgr.shape[:2]
    annotated = image_bgr.copy()
    cv2.rectangle(annotated, (int(.05*w),int(.35*h)), (int(.48*w),int(.75*h)), (70,190,140), 3)
    cv2.rectangle(annotated, (int(.55*w),int(.30*h)), (int(.95*w),int(.80*h)),
                  (50,80,220) if result=="POSITIVE" else (70,170,80) if result=="NEGATIVE" else (0,170,220), 3)
    cv2.putText(annotated, "REFERENCE", (int(.05*w),max(25,int(.35*h)-10)), cv2.FONT_HERSHEY_SIMPLEX,.65,(70,190,140),2)
    cv2.putText(annotated, "TEST REGION", (int(.55*w),max(25,int(.30*h)-10)), cv2.FONT_HERSHEY_SIMPLEX,.65,(50,80,220),2)
    cv2.putText(annotated, result, (25,45), cv2.FONT_HERSHEY_SIMPLEX,1.2,(40,40,220),3)

    return {
        "result": result,
        "confidence": round(float(confidence),1),
        "explanation": explanation,
        "sample_rgb": {"r":round(float(r),1),"g":round(float(g),1),"b":round(float(b),1)},
        "sample_hsv": {"h":round(hue,1),"s":round(sat,1),"v":round(val,1)},
        "reference_brightness": round(card_v,1) if card else None,
        "lighting_factor": round(light_factor,3),
        "annotated": annotated
    }
