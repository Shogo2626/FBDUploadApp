from flask import Flask, render_template, request, send_file, session
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使用するための設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# マッピングデータ
country_mapping = {
    "中国": "156", "インド": "356", "パキスタン": "586", "バングラデシュ": "050",
    "インドネシア": "360", "タイ": "764", "ベトナム": "704", "アメリカ": "840",
    "ウズベキスタン": "860", "韓国": "410", "台湾": "158", "日本": "392"
}

mapping_data = {
    "Adjuster": {"サービス技師": "AD01", "お客様": "AD02"},
    "ICS Usage": {
        "ICS設定値から調整": "IU01", "既存設定値から調整": "IU02", 
        "ICS設定値から変更なし": "IU03", "ICS不使用（手動設定）": "IU04", "不明": "IU05"
    },
    "Running Judge": {"合格": "RJ01", "不合格": "RJ02", "不明": "RJ03"},
    "Quality Judge": {"合格": "QJ01", "不合格": "QJ02", "不明": "QJ03"}
}

category_mapping = {
    "稼動-経停台低減": ["リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間", "経糸止装置内", "経糸止装置～ビーム間"],
    "稼動-緯停台低減": ["入口くぐり", "入口ループ", "大ループ", "エンドループ", "エンドちぢれ",
                        "先端飛びだし", "途中切れ", "捨耳掴まず", "上糸くぐり", "下糸くぐり", 
                        "ムダ止まり", "ロングピック（長尺）", "ショートピック（短尺）",
                        "ドラム～メイン間切れ", "カッターミス", "先端切れ (吹き切れ)", "張り切れ"],
    "品質-経方向": ["経糸緩み", "エアーマーク", "サブノズルマーク", "経筋", "布破れ", "地合い不良"],
    "品質-緯方向": ["緯糸緩み(左側)", "緯糸緩み(右側)", "筬打ち切れ", "テンプル切れ", 
                    "フィラメント切れ", "繊維割れ", "ビリ", "左右色差"],
    "品質-耳欠点": ["耳吊り", "耳緩み", "耳フレア"],
    "品質-止段": ["前厚段-全幅", "後厚段-全幅", "前薄段-全幅", "後薄段-全幅",
                   "前厚段-テンプル", "後厚段-テンプル", "前薄段-テンプル", "後薄段-テンプル",
                   "前枕段", "後枕段", "ループ段"]
}

change_areas = [
    "バック", "ドロッパ", "イージング", "テンプル", "耳", 
    "緯入れ-メイン系", "カッター", "開口角", "開口量", 
    "枠高さ", "ドエル", "クロスタイミング", "エア圧力", 
    "タオル", "緯入れ-サブ系", "張力", "Motor設定", 
    "MARK設定", "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"
]

# ********************************************************************************
# ファイルアップロード画面
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename:
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)
            session["current_file"] = uploaded_file.filename
            return render_template("basic_info.html", file_name=uploaded_file.filename, countries=country_mapping.keys())
    return render_template("upload.html")

# ********************************************************************************
# 基本情報入力画面
# ********************************************************************************
@app.route("/basic_info", methods=["POST"])
def basic_info():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が見つかりません", 400

    # 基本情報保存
    basic_info = {
        "customer": request.form["customer"],
        "country": country_mapping.get(request.form["country"], ""),
        "reporter": request.form["reporter"],
        "adjuster": mapping_data["Adjuster"].get(request.form["adjuster"], ""),
        "ics_usage": mapping_data["ICS Usage"].get(request.form["ics_usage"], ""),
        "running": mapping_data["Running Judge"].get(request.form["running"], ""),
        "quality": mapping_data["Quality Judge"].get(request.form["quality"], "")
    }
    session["basic_info"] = basic_info
    session["phenomena"] = []  # 現象データ初期化

    return render_template("phenomenon.html", categories=category_mapping, change_areas=change_areas, phenomena=[])

# ********************************************************************************
# 現象データ入力画面
# ********************************************************************************
@app.route("/phenomenon", methods=["POST"])
def phenomenon_input():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が見つかりません", 400

    category = request.form["category"]
    subcategory = request.form["subcategory"]
    change_area = request.form["change_area"]
    phenomena = session.get("phenomena", [])
    phenomena.append((category, subcategory, change_area))
    session["phenomena"] = phenomena

    return render_template("phenomenon.html", categories=category_mapping, change_areas=change_areas, phenomena=session["phenomena"])

# ********************************************************************************
# データ保存処理
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が見つかりません", 400

    phenomenon_data = session.get("phenomena", [])
    basic_info = session.get("basic_info", {})

    # ファイルのエンコーディングを検出
    original_file_path = os.path.join(UPLOAD_FOLDER, file_name)
    processed_file_path = f"processed_{file_name}"

    phenomenon_lines = ['"JAT910-Phenomenon DATA -----------"\n']
    for category, subcategory, change_area in phenomenon_data:
        mapped_subcategory = subcategory_mapping.get(subcategory, subcategory)
        mapped_change_area = change_areas.index(change_area) + 1
        phenomenon_lines.append(f'"{category}","{mapped_subcategory}","{mapped_change_area}"\n')

    # ファイル書き込み処理
    with open(original_file_path, "r", encoding="utf-8") as original, open(processed_file_path, "w", encoding="utf-8") as processed:
        processed.writelines(original.readlines())  # 元データ
        processed.writelines(phenomenon_lines)  # 現象データ

    return send_file(processed_file_path, as_attachment=True)

# ********************************************************************************
# サーバー起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)