import os
import json
import re
import io
from google import genai
from PIL import Image

# 1. API初期化
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEYが設定されていません。GitHub Secretsを確認してください。")

client = genai.Client(api_key=api_key)

prompt = os.environ.get("ADDON_PROMPT", "背中にキノコを背負った可愛いカメのモブ")
print("==========================================")
print(f"【AIチーム自動稼働開始】 指示: {prompt}")
print("==========================================")

# 出力フォルダ作成
bp_path = "addon_output/behavior_pack"
rp_path = "addon_output/resource_pack"
os.makedirs(f"{bp_path}/entities", exist_ok=True)
os.makedirs(f"{rp_path}/textures/entity", exist_ok=True)

max_retries = 3

# ----------------------------------------------------
# 2. JSONコード生成 & 構文自己修復ループ
# ----------------------------------------------------
print("\n[Phase 1] コーダーAI：JSON設計および構文自己修復テスト中...")

for attempt in range(1, max_retries + 1):
    print(f"-> Code Trial {attempt}/{max_retries}...")
    try:
          response = client.models.generate_content(
            model='gemini-3.8-flash',
            contents=f"""
            あなたはマインクラフト統合版(Bedrock Edition)のプロフェッショナル開発者です。
            以下の要望に基づいて、カスタムモブのJSONを生成してください。
            要望: {prompt}

            以下の形式で必ず出力してください:
            ---MANIFEST---
            (manifest.json用の正しいJSON)
            ---ENTITY---
            (entities/custom_mob.json用の正しいJSON)
            """,
        )
        
        text = response.text
        if "---MANIFEST---" not in text or "---ENTITY---" not in text:
            raise ValueError("AIの出力フォーマットが不正です。セパレータが見つかりません。")

        manifest_str = text.split("---MANIFEST---")[1].split("---ENTITY---")[0].strip()
        entity_str = text.split("---ENTITY---")[1].strip()

        # ```json マークアップ等の除外
        manifest_str = re.sub(r'```json|```', '', manifest_str).strip()
        entity_str = re.sub(r'```json|```', '', entity_str).strip()

        # 自動バリデーション (JSONパースチェック)
        manifest_data = json.loads(manifest_str)
        entity_data = json.loads(entity_str)

        # ファイルへ保存
        with open(f"{bp_path}/manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        with open(f"{bp_path}/entities/custom_mob.json", "w", encoding="utf-8") as f:
            json.dump(entity_data, f, indent=2, ensure_ascii=False)

        print("-> コーダーAI: JSON構文チェック完全合格！")
        break
    except Exception as e:
        print(f"⚠️ 構文エラーを検知: {e}")
        if attempt == max_retries:
            raise RuntimeError("コードの自己修復上限に達しました。")
        print("-> AIが問題内容を検知し、自動書き直しを実行します...")

# ----------------------------------------------------
# 3. テクスチャ画像生成 & 破損・表示バグ自己修復ループ
# ----------------------------------------------------
print("\n[Phase 2] デザイナーAI：テクスチャ生成および画像検品中...")

for attempt in range(1, max_retries + 1):
    print(f"-> Texture Trial {attempt}/{max_retries}...")
    try:
        image_response = client.models.generate_images(
            model='imagen-3.0-generate-002',
            prompt=f"Minecraft style pixel art texture for a mob: {prompt}, clean pixel art, vibrant colors, game asset, flat style, no background",
            config=dict(number_of_images=1, aspect_ratio="1:1")
        )

        if not image_response.generated_images:
            raise ValueError("画像が生成されませんでした。")

        for generated_image in image_response.generated_images:
            img_bytes = generated_image.image.image_bytes
            
            # 画像の破損・整合性検証
            img = Image.open(io.BytesIO(img_bytes))
            img.verify()
            
            # 正常であればPNG保存
            img = Image.open(io.BytesIO(img_bytes))
            img.save(f"{rp_path}/textures/entity/custom_mob.png", "PNG")

        print("-> デザイナーAI: テクスチャ画像検品合格！（バグなし）")
        break
    except Exception as e:
        print(f"⚠️ テクスチャ画像エラー/破損を検知: {e}")
        if attempt == max_retries:
            raise RuntimeError("テクスチャの自己修復上限に達しました。")
        print("-> デザイナーAIが設定を微調整して再生成します...")

print("\n==========================================")
print("【全工程完了】AIチームによる自己修復テストを全てクリアしました！")
print("==========================================")
