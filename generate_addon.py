import os
import json
import re
import base64
from google import genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEYが設定されていません。")

client = genai.Client(api_key=api_key)
prompt = os.environ.get("ADDON_PROMPT", "可愛いモンスター")

print("==========================================")
print(f"【汎用AI工場稼働】 指示: {prompt}")
print("==========================================")

bp_path = "addon_output/behavior_pack"
rp_path = "addon_output/resource_pack"
os.makedirs(f"{bp_path}/entities", exist_ok=True)
os.makedirs(f"{rp_path}/entity", exist_ok=True)
os.makedirs(f"{rp_path}/textures/entity", exist_ok=True)

# ----------------------------------------------------
# 1. コーダーAI：プロンプトから固有のIDやJSONを完全に動的生成
# ----------------------------------------------------
print("\n[Phase 1] コーダーAI：プロンプトを分析して専用JSONを設計中...")

max_retries = 3
bp_entity = None
bp_manifest = None
rp_client_entity = None
rp_manifest = None
entity_id = "custom:mob"

for attempt in range(1, max_retries + 1):
    print(f"-> Code Trial {attempt}/{max_retries}...")
    try:
        response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=f"""
            あなたはマインクラフト統合版(Bedrock Edition)の高度なアドオン開発AIです。
            以下のユーザーの要望に基づいて、このモブ専用のビヘイビアーパックとリソースパックのJSONを設計してください。
            要望: {prompt}

            以下の4つのセクションに分けて、それぞれ正確なJSON形式で出力してください（マークダウンの ```json や ``` は除外するか、パース可能なようにしてください）。

            ---BP_MANIFEST---
            (ビヘイビアーパックの manifest.json のJSON。uuidはユニークなUUIDv4を生成すること)
            ---BP_ENTITY---
            (ビヘイビアーパックの entities/ 内のモブ定義JSON。
             identifierは "custom:任意の英語小文字名" (例: custom:fire_penguin) にし、
             is_spawnable: true, is_summonable: true にし、歩行や体力などの基本的なコンポーネントを含めること)
            ---RP_MANIFEST---
            (リソースパックの manifest.json のJSON。uuidは別のユニークなUUIDv4を生成すること)
            ---RP_CLIENT_ENTITY---
            (リソースパックの entity/ 内のクライアント定義JSON。
             identifierは上記と同じにし、materials.default は "pig" や "cow" や "turtle" などの既存バニラモデルを指定し、
             textures.default は "textures/entity/custom_mob" とし、
             spawn_egg のカラーを設定すること)
            """,
        )
        
        text = response.text
        if not all(k in text for k in ["---BP_MANIFEST---", "---BP_ENTITY---", "---RP_MANIFEST---", "---RP_CLIENT_ENTITY---"]):
            raise ValueError("必要なセパレータがレスポンスに含まれていません。")

        # 各セクションの切り出しとパース
        bp_man_str = text.split("---BP_MANIFEST---")[1].split("---BP_ENTITY---")[0].strip()
        bp_ent_str = text.split("---BP_ENTITY---")[1].split("---RP_MANIFEST---")[0].strip()
        rp_man_str = text.split("---RP_MANIFEST---")[1].split("---RP_CLIENT_ENTITY---")[0].strip()
        rp_cli_str = text.split("---RP_CLIENT_ENTITY---")[1].strip()

        bp_man_str = re.sub(r'```json|```', '', bp_man_str).strip()
        bp_ent_str = re.sub(r'```json|```', '', bp_ent_str).strip()
        rp_man_str = re.sub(r'```json|```', '', rp_man_str).strip()
        rp_cli_str = re.sub(r'```json|```', '', rp_cli_str).strip()

        bp_manifest = json.loads(bp_man_str)
        bp_entity = json.loads(bp_ent_str)
        rp_manifest = json.loads(rp_man_str)
        rp_client_entity = json.loads(rp_cli_str)

        # 動的に生成された識別子（identifier）を抽出
        try:
            entity_id = bp_entity["minecraft:entity"]["description"]["identifier"]
        except (KeyError, TypeError):
            pass

        print(f"-> コーダーAI: 動的JSON設計合格！ (識別子: {entity_id})")
        break
    except Exception as e:
        print(f"⚠️ エラー検知: {e}")
        if attempt == max_retries:
            raise RuntimeError("コードの自己修復上限に達しました。")
        print("-> 再生成します...")

# ファイル書き出し
with open(f"{bp_path}/manifest.json", "w", encoding="utf-8") as f:
    json.dump(bp_manifest, f, indent=2, ensure_ascii=False)

# エンティティファイル名は識別子の後半を使う（例: custom:fire_penguin -> fire_penguin.json）
file_name = entity_id.split(":")[-1] if ":" in entity_id else "custom_mob"
with open(f"{bp_path}/entities/{file_name}.json", "w", encoding="utf-8") as f:
    json.dump(bp_entity, f, indent=2, ensure_ascii=False)

with open(f"{rp_path}/manifest.json", "w", encoding="utf-8") as f:
    json.dump(rp_manifest, f, indent=2, ensure_ascii=False)

with open(f"{rp_path}/entity/{file_name}.json", "w", encoding="utf-8") as f:
    json.dump(rp_client_entity, f, indent=2, ensure_ascii=False)

# テクスチャのプレースホルダー配置
fallback_png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")
with open(f"{rp_path}/textures/entity/custom_mob.png", "wb") as f:
    f.write(fallback_png)

print(f"==========================================")
print(f"【汎用ビルド完了】 ID: {entity_id}")
print(f"==========================================")
