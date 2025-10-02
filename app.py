from flask import Flask, render_template, request, send_file, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 選択肢データ
countries = ["中国", "インド", "パキスタン", "バングラデシュ", "インドネシア", "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"]
adjusters = ["サービス技師", "お客様"]
ics_usages = ["ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし", "ICS不使用（手動設定）", "不明"]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

# 選択肢データ（小分類と英語表記の対応）
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
    "先端飛びだし": "Leading edge flying out",
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
    "左右色差": "Color difference (LH and RH)",
    "耳吊り": "Selvage pulling",
    "耳緩み": "Selvage loose",
    "耳フレア": "Selvage flare",
    "前厚段-全幅": "Front thick mark - full width",
    "後厚段-全幅": "Rear thick mark - full width",
    "前薄段-全幅": "Front thin mark - full width",
    "後薄段-全幅": "Rear thin mark - full width",
    "前厚段-テンプル": "Front thick mark - temple",
    "後厚段-テンプル": "Rear thick mark - temple",
    "前薄段-テンプル": "Front thin mark - temple",
    "後薄段-テンプル": "Rear thin mark - temple",
    "前枕段": "Front corrugated mark",
    "後枕段": "Rear corrugated mark",
    "ループ段": "Loop mark"
}

# 変更箇所とコードの対応
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

# ********************************************************************************
# メイン画面（ファイルアップロード）
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        if uploaded_file.filename != "":
            file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
            uploaded_file.save(file_path)  # ファイル保存
            session["current_file"] = uploaded_file.filename  # 状態をセッションで管理
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
# 現象入力データの処理と保存
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    file_name = session.get("current_file")
    if not file_name:
        return "エラー: ファイル名がありません！", 400

    file_path = os.path.join(UPLOAD_FOLDER, file_name)
    if not os.path.exists(file_path):
        return f"エラー: ファイルが見つかりません！（{file_path}）", 400

    final_file_path = os.path.join(UPLOAD_FOLDER, f"final_{file_name}")

    # 現象データを収集して書き出し
    phenomenon_data = session.get("phenomena", [])
    write_to_file(phenomenon_data, final_file_path)

    return send_file(final_file_path, as_attachment=True)

# ********************************************************************************
# 外部ファイル書き込み処理
# ********************************************************************************
def write_to_file(phenomenon_data, output_path):
    """現象データを英語表記およびコードマッピングに基づき書き込む処理"""
    phenomenon_dict = {}
    for category, subcategory, change_area in phenomenon_data:
        if subcategory not in phenomenon_dict:
            phenomenon_dict[subcategory] = []
        phenomenon_dict[subcategory].append(change_area_mapping.get(change_area, "CC00"))

    lines = ['"JAT910-Phenomenon DATA -----------"\n']
    for subcategory, english_term in subcategory_mapping.items():
        codes = phenomenon_dict.get(subcategory, [])
        change_codes = ",".join(f'"{code}"' for code in codes)
        if codes:
            lines.append(f'"{english_term}","1",{change_codes}\n')
        else:
            lines.append(f'"{english_term}","0","0"\n')

    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.writelines(lines)

if __name__ == "__main__":
    app.run(debug=True)