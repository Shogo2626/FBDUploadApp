from flask import Flask, render_template, request, send_file, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使うために必要な設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # アップロード先フォルダを作成

# 選択肢データ
countries = [
    "中国", "インド", "パキスタン", "バングラデシュ", "インドネシア",
    "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"
]

adjusters = ["サービス技師", "お客様"]
ics_usages = [
    "ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし",
    "ICS不使用（手動設定）", "不明"
]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

# 更新された選択肢データ
category_mapping = {
    "稼動-経停台低減": [
        "リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間",
        "経糸止装置内", "経糸止装置～ビーム間"
    ],
    "稼動-緯停台低減": [
        "入口くぐり", "入口ループ", "大ループ", "エンドループ", "エンドちぢれ",
        "先端飛びだし", "途中切れ", "捨耳掴まず", "上糸くぐり", "下糸くぐり",
        "ムダ止まり", "ロングピック（長尺）", "ショートピック（短尺）",
        "ドラム～メイン間切れ", "カッターミス", "先端切れ (吹き切れ)", "張り切れ"
    ],
    "品質-経方向": [
        "経糸緩み", "エアーマーク", "サブノズルマーク", "経筋", "布破れ", "地合い不良"
    ],
    "品質-緯方向": [
        "緯糸緩み(左側)", "緯糸緩み(右側)", "筬打ち切れ", "テンプル切れ",
        "フィラメント切れ", "繊維割れ", "ビリ", "左右色差"
    ],
    "品質-耳欠点": ["耳吊り", "耳緩み", "耳フレア"],
    "品質-止段": [
        "前厚段-全幅", "後厚段-全幅", "前薄段-全幅", "後薄段-全幅",
        "前厚段-テンプル", "後厚段-テンプル", "前薄段-テンプル", "後薄段-テンプル",
        "前枕段", "後枕段", "ループ段"
    ]
}

change_areas = [
    "バック", "ドロッパ", "イージング", "テンプル", "耳", "緯入れ-メイン系",
    "カッター", "開口角", "開口量", "枠高さ", "ドエル", "クロスタイミング",
    "エア圧力", "タオル", "緯入れ-サブ系", "張力", "Motor設定", "MARK設定",
    "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"
]

# ********************************************************************************
# アップロードページ
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)  # ファイルを保存
            session["current_file"] = uploaded_file.filename  # セッションにファイル名を保存
            return render_template(
                "form.html",
                file_name=uploaded_file.filename,
                countries=countries,
                adjusters=adjusters,
                ics_usages=ics_usages,
                running_judgments=running_judgments,
                quality_judgments=quality_judgments
            )
    return render_template("upload.html")

# ********************************************************************************
# ファイル内容を整理して保存
# ********************************************************************************
def process_and_save_phenomenon(file_path, phenomenon_data, basic_info):
    """現象データと基本情報を処理してファイルを更新する"""
    subcategory_dict = {}
    for category, subcategory, change_area in phenomenon_data:
        if subcategory not in subcategory_dict:
            subcategory_dict[subcategory] = []
        subcategory_dict[subcategory].append(change_area_mapping.get(change_area, "CC00"))

    # 現象データを英語でフォーマット
    new_lines = ['"JAT910-Phenomenon DATA -----------"\n']
    for subcategory, english_term in subcategory_mapping.items():
        key_changes = ", ".join(f'"{code}"' for code in subcategory_dict.get(subcategory, []))
        if key_changes:
            new_lines.append(f'"{english_term}","1",{key_changes}\n')
        else:
            new_lines.append(f'"{english_term}","0","0"\n')

    updated_content = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            updated_content.append(line)
            if "JAT700-MCARD-DATA file_info -----------" in line:
                updated_content.append(f'"Customer","{basic_info["customer"]}"\n')
                updated_content.append(f'"Country","{basic_info["country"]}"\n')
                updated_content.append(f'"Reporter","{basic_info["reporter"]}"\n')
                updated_content.append(f'"Adjuster","{basic_info["adjuster"]}"\n')
                updated_content.append(f'"ICS Usage","{basic_info["ics_usage"]}"\n')
                updated_content.append(f'"Running","{basic_info["running"]}"\n')
                updated_content.append(f'"Quality","{basic_info["quality"]}"\n')

    # 新ファイルへ保存
    output_path = f"processed_{os.path.basename(file_path)}"
    with open(os.path.join(UPLOAD_FOLDER, output_path), "w", encoding="utf-8") as file:
        file.writelines(new_lines)
        file.writelines(updated_content)

    return output_path

# ********************************************************************************
# 現象データ保存エンドポイント
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が提供されていません", 400
    
    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return f"エラー: ファイルが見つかりません ({file_path})", 400
    
    # 基本情報を取得
    basic_info = {
        "customer": request.form["customer_name"],
        "country": request.form["country"],
        "reporter": request.form["reporter"],
        "adjuster": request.form["adjuster"],
        "ics_usage": request.form["ics_usage"],
        "running": request.form["running"],
        "quality": request.form["quality"]
    }
    # 現象データを取得
    phenomenon_data = session.get("phenomena", [])
    
    # ファイルの処理と保存
    processed_file_path = process_and_save_phenomenon(file_path, phenomenon_data, basic_info)
    return send_file(processed_file_path, as_attachment=True)

# ********************************************************************************
# サーバー起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)