#!/usr/bin/env python3
import asyncio
import json
from pathlib import Path
from datetime import datetime
import httpx

API_ROOT = "http://127.0.0.1:8000"
DATA_DIR = Path("publications/synthetic_lethality/results/parp_data_search/open_access")
CACHE_DIR = Path("publications/synthetic_lethality/results/parp_data_search/validation_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

BATCH_SIZES = [10, 25, 50, 100, 131]

def load_patients():
    with open(DATA_DIR / "profound_patients_cleaned.json", 'r') as f:
        return json.load(f)['patients']

async def validate_batch(patients, batch_size):
    cache_file = CACHE_DIR / f"profound_batch_{batch_size}.json"
    
    if cache_file.exists():
        print(f"\n✅ Batch {batch_size}: Cached")
        with open(cache_file, 'r') as f:
            result = json.load(f)
            print(f"   Accuracy: {result.get('accucy', 0):.1f}%")
            return result
    
    print(f"\n{'=' * 70}")
    print(f"BATCH {batch_size} - Processing {batch_size} patients")
    print(f"{'=' * 70}")
    
    batch = patients[:batch_size]
    results = []
    correct = 0
    total = 0
    
    for i, patient in enumerate(batch, 1):
        patient_id = patient['patient_id']
        print(f"   [{i:3d}/{len(batch)}] {patient_id}...", end=" ", flush=True)
        
        mutations = []
        for mut in patient.get('mutations', []):
            mutations.append({
                "gene": mut['gene'],
                "hgvs_p": "p.?",
                "chrom": "?",
                "pos": 0,
                "ref": "?",
                "alt": "?",
                "consequence": "unknown"
            })
        
        payload = {
            "mutations": mutations,
            "disease": "prostate_cancer",
            "options": {
                "panel_id": "sl_publication",
                "ablation_mode": "SP",
                "adaptive": True
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(f"{API_ROOT}/api/efficacy/predict", json=payload)
                resp.raise_for_status()
                response = resp.json()
        except Exception as e:
            print(f"❌ ERROR")
            results.append({"case_id": patient_id, "error": str(e)})
            continue
        
        drugs = response.get('drugs', [])
        top_drug = drugs[0].get('name', 'NONE') if drugs else 'NONE'
        top_conf = drugs[0].get('confidence', 0.0) if drugs else 0.0
        
        gt_drugs = ["Olaparib", "Niraparib", "Rucaparib"]
        is_correct = any(gt.lower() in top_drug.lower() for gt in gt_drugs) or "parp" in top_drug.lower()
        
        if is_correct:
            correct += 1
        total += 1
        
        results.append({
            "case_id": patient_id,
            "group": patient.get('group'),
            "prediction": {"top_dr": top_drug, "confidence": top_conf},
            "correct": is_correct
        })
        
        print(f"{'✅' if is_correct else '❌'} {top_drug}")
        await asyncio.sleep(0.3)
    
    accuracy = (correct / total * 100) if total > 0 else 0.0
    
    result = {
        "batch_size": batch_size,
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "timestamp": datetime.now().isoformat(),
        "results": results
    }
    
    with open(cache_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n   ✅ Batch {batch_size}: {accuracy:.1f}% ({correct}/{total})")
    return result

async def main():
    print("=" * 70)
    print("PROfound VALIDATION - BATCHED WITH CACHING")
    print("=" * 70)
    
    patients = load_patients()
    print(f"\n✅ Loaded {len(patients)} patients")
    
    all_results = {}
    for batch_size in BATCH_SIZES:
        if batch_size > len(patients):
            continue
        result = await validate_batch(patients, batch_size)
        all_results[batch_size] = result
    
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    for bs in sorted(all_results.keys()):
        r = all_results[bs]
        print(f"   Batch {bs:3d}: {r['accuracy']:5.1f}% ({r['correct']:3d}/{r['total']:3d})")

if __name__ == "__main__":
    asyncio.run(main())
