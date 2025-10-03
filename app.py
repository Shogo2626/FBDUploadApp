from flask import Flask, render_template, request, send_file, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッションを使用するための設定
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
    "経筋": "Warp streaks",
    "布破れ": "Fabric tear",
    "地合い不良": "Irregular fabric texture",
    "緯糸緩み(右側)": "Weft loose(RH)",
    "エアーマーク": "Air mark",
    "サブノズルマーク": "Sub nozzle mark",
    "筬打ち切れ": "Beating weft break",
    "テンプル切れ": "Temple weft break",
}

change_area_mapping = {
    "バック": "CC01",
    "ドロッパ": "CC02",
    "イージング": "CC03",
    "テンプル": "CC04",
    "耳": "CC05",
    "緯入れ-メイン系": "CC06",
    "カッター": "CC07",
    "その他": "CC22"
}

countries = [
    "中国", "インド", "パキスタン", "バングラデシュ",
    "インドネシア", "タイ", "ベトナム", "アメリカ", 
    "ウズベキスタン", "韓国", "台湾", "日本"
]
adjusters = ["サービス技師", "お客様"]
ics_usages = [
    "ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし",
    "ICS不使用（手動設定）", "不明"
]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

# ********************************************************************************
# ファイルアップロードページ
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    try:
        if request.method == "POST":
            uploaded_file = request.files["file"]
            if uploaded_file.filename:
                file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                uploaded_file.save(file_path)  # ファイル保存
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
    except Exception as e:
        print("エラー:", str(e))  # デバッグ情報
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 基本情報入力ページ
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_data():
    try:
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("エラー: ファイルがセッションに存在しません")

        # フォームからの情報を保存
        basic_info = {
            "customer": request.form.get("customer_name", ""),
            "country": request.form.get("country", ""),
            "reporter": request.form.get("reporter", ""),
            "adjuster": request.form.get("adjuster", ""),
            "ics_usage": request.form.get("ics_usage", ""),
            "running": request.form.get("running", ""),
            "quality": request.form.get("quality", "")
        }
        session["basic_info"] = basic_info
        session["phenomena"] = []  # 現象データを初期化

        # 現象データ入力画面を表示
        return render_template(
            "phenomenon.html",
            categories=subcategory_mapping.keys(),
            change_areas=change_area_mapping.keys(),
            phenomena=[]
        )
    except Exception as e:
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 現象データ入力ページ
# ********************************************************************************
@app.route("/phenomenon", methods=["POST"])
def phenomenon_input():
    try:
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("エラー: ファイル名が見つかりません")

        # 現象データ入力を処理
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        change_area = request.form["change_area"]
        phenomena = session.get("phenomena", [])
        phenomena.append((category, subcategory, change_area))
        session["phenomena"] = phenomena

        return render_template(
            "phenomenon.html",
            categories=subcategory_mapping.keys(),
            change_areas=change_area_mapping.keys(),
            phenomena=session["phenomena"]
        )
    except Exception as e:
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 現象データ保存
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    try:
        file_name = session.get("current_file")
        if not file_name:
            return "エラー: ファイル名が指定されていません", 400

        phenomenon_data = session.get("phenomena", [])
        processed_file_path = os.path.join(UPLOAD_FOLDER, f"processed_{file_name}")

        phenomenon_lines = ['"JAT910-Phenomenon DATA -----------"\n']
        for _, subcategory, change_area in phenomenon_data:
            mapped_subcategory = subcategory_mapping.get(subcategory, "Unknown")
            mapped_change_area = change_area_mapping.get(change_area, "CC00")
            phenomenon_lines.append(f'"{mapped_subcategory}","1","{mapped_change_area}"\n')

        with open(processed_file_path, "w", encoding="utf-8") as output_file:
            with open(os.path.join(UPLOAD_FOLDER, file_name), "r", encoding="utf-8") as input_file:
                output_file.writelines(input_file.readlines())
            output_file.writelines(phenomenon_lines)

        return send_file(processed_file_path, as_attachment=True)
    except Exception as e:
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# サーバー起動
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)