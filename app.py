from flask import Flask, render_template, request, send_file, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使うために必要な設定
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 各種マッピングデータ
subcategory_mapping = {
    "リード揺動範囲": "Within reed oscillation range",
    "綜絖枠内": "Within heald frame",
    "最終綜絖枠～経糸止装置間": "Between final heald frame and warp stop motion",
    "経糸止装置内": "Within warp stop motion",
    "経糸止装置～ビーム間": "Between warp stop motion and beam",
    "入口くぐり": "Inlet underpass",
    "入口ループ": "Loop at inlet",
    "大ループ": "Large loop",
    "エンドループ": "End loop",
    "エンドちぢれ": "End curl",
    "先端飛びだし": "Leading edge flying-out",
    "途中切れ": "Broken halfway",
    "捨耳掴まず": "Failure in catching waste selvage",
    "上糸くぐり": "Passing above upper warp",
    "下糸くぐり": "Passing above lower warp",
    "ムダ止まり": "False stop",
    "ロングピック（長尺）": "Long pick",
    "ショートピック（短尺）": "Short pick",
    "ドラム～メイン間切れ": "Broken between drum and main nozzle",
    "カッターミス": "Cutting failure",
    "先端切れ (吹き切れ)": "Broken leading end",
    "経糸緩み": "Warp loose on fabric",
    "エアーマーク": "Air mark",
    "サブノズルマーク": "Sub nozzle mark",
    "経筋": "Warp streaks",
    "布破れ": "Fabric tear",
    "地合い不良": "Irregular fabric texture",
    "緯糸緩み(左側)": "Weft loose(LH)",
    "緯糸緩み(右側)": "Weft loose(RH)",
    "筬打ち切れ": "Beating weft break",
    "テンプル切れ": "Temple weft break",
    "フィラメント切れ": "Broken filament",
    "繊維割れ": "Filament splitting",
    "ビリ": "Weft overlapping",
    "左右色差": "Color difference(LH and RH)",
    "耳吊り": "Selvage pulling",
    "耳緩み": "Selvage loose",
    "耳フレア": "Selvage flare",
    "前厚段-全幅": "Front thick Mark-Full width",
    "後厚段-全幅": "Rear thick Mark-Full width",
    "前薄段-全幅": "Front thin Mark-Full width",
    "後薄段-全幅": "Rear thin Mark-Full width",
    "前厚段-テンプル": "Front thick Mark-Temple",
    "後厚段-テンプル": "Rear thick Mark-Temple",
    "前薄段-テンプル": "Front thin Mark-Temple",
    "後薄段-テンプル": "Rear thin Mark-Temple",
    "前枕段": "Front Corrugated Mark",
    "後枕段": "Rear Corrugated Mark",
    "ループ段": "Loop Mark"
}

change_area_mapping = {
    "バック": "CC01",
    "ドロッパ": "CC02",
    "イージング": "CC03",
    "テンプル": "CC04",
    "耳": "CC05",
    "緯入れ-メイン系": "CC06",
    "カッター": "CC07",
    "開口角": "CC08",
    "開口量": "CC09",
    "枠高さ": "CC10",
    "ドエル": "CC11",
    "クロスタイミング": "CC12",
    "エア圧力": "CC13",
    "タオル": "CC14",
    "緯入れ-サブ系": "CC15",
    "張力": "CC16",
    "Motor設定": "CC17",
    "MARK設定": "CC18",
    "T0-Tw": "CC19",
    "Tw-Ctrl": "CC20",
    "フィーラ設定": "CC21",
    "その他": "CC22"
}

# 基本情報をユーザーが選択可能な選択肢
countries = ["中国", "インド", "パキスタン", "バングラデシュ", "インドネシア", "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"]
adjusters = ["サービス技師", "お客様"]
ics_usages = ["ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし", "ICS不使用（手動設定）", "不明"]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

category_mapping_ui = {
    "稼動-経停台低減": subcategory_mapping.keys(),
    "稼動-緯停台低減": subcategory_mapping.keys(),
    "品質-経方向": subcategory_mapping.keys(),
    "品質-緯方向": subcategory_mapping.keys()
}

change_areas_ui = list(change_area_mapping.keys())

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
# 基本情報入力画面と保存
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_data():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が指定されていません", 400

    # ユーザー入力データを保存
    basic_info = {
        "customer": request.form["customer_name"],
        "country": request.form["country"],
        "reporter": request.form["reporter"],
        "adjuster": request.form["adjuster"],
        "ics_usage": request.form["ics_usage"],
        "running": request.form["running"],
        "quality": request.form["quality"]
    }
    session["basic_info"] = basic_info

    # 現象入力画面を表示
    session["phenomena"] = []
    return render_template(
        "phenomenon.html",
        file_name=file_name,
        categories=category_mapping_ui,
        change_areas=change_areas_ui,
        phenomena=session["phenomena"]
    )

# ********************************************************************************
# 現象データ入力画面
# ********************************************************************************
@app.route("/phenomenon", methods=["GET", "POST"])
def phenomenon_input():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が指定されていません", 400

    if request.method == "POST":
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        change_area = request.form["change_area"]
        phenomena = session.get("phenomena", [])
        phenomena.append((category, subcategory, change_area))
        session["phenomena"] = phenomena

    return render_template(
        "phenomenon.html",
        file_name=file_name,
        categories=category_mapping_ui,
        change_areas=change_areas_ui,
        phenomena=session["phenomena"]
    )

# ********************************************************************************
# 現象データ保存
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名が指定されていません", 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return f"エラー: ファイルが見つかりません ({file_path})", 400

    # データ変換
    phenomenon_data = session.get("phenomena", [])
    phenomenon_dict = {}
    for _, subcategory, change_area in phenomenon_data:
        mapped_subcategory = subcategory_mapping.get(subcategory, subcategory)
        mapped_change_area = change_area_mapping.get(change_area, "CC00")
        if mapped_subcategory not in phenomenon_dict:
            phenomenon_dict[mapped_subcategory] = []
        phenomenon_dict[mapped_subcategory].append(mapped_change_area)

    phenomenon_lines = ['"JAT910-Phenomenon DATA -----------"\n']
    for subcategory, areas in phenomenon_dict.items():
        phenomenon_lines.append(f'"{subcategory}","1",{",".join(areas)}\n')

    # ファイル保存
    processed_file_name = f"processed_{file_name}"
    processed_file_path = os.path.join(UPLOAD_FOLDER, processed_file_name)
    with open(processed_file_path, "w", encoding="utf-8") as file:
        with open(file_path, "r", encoding="utf-8") as original_file:
            file.writelines(original_file.readlines())  # 元データ
        file.writelines(phenomenon_lines)

    return send_file(processed_file_path, as_attachment=True)

# ********************************************************************************
# サーバーの起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)