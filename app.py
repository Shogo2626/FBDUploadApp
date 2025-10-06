from flask import Flask, render_template, request, send_file, session
import os

app = Flask(__name__)

# セッションのためのキー設定
app.secret_key = 'your_secret_key'

# アップロード先ディレクトリ
UPLOAD_FOLDER = "./uploaded_files"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 選択肢データ
countries = [
    "中国", "インド", "パキスタン", "バングラデシュ", "インドネシア",
    "タイ", "ベトナム", "アメリカ", "ウズベキスタン", "韓国", "台湾", "日本"
]

adjusters = ["サービス技師", "お客様"]
ics_usages = ["ICS設定値から調整", "既存設定値から調整", "ICS設定値から変更なし", "ICS不使用（手動設定）", "不明"]
running_judgments = ["合格", "不合格", "不明"]
quality_judgments = ["合格", "不合格", "不明"]

category_mapping = {
    "稼動-経停台低減": ["リード揺動範囲", "綜絖枠内", "最終綜絖枠～経糸止装置間", "経糸止装置内", "経糸止装置～ビーム間"],
    "稼動-緯停台低減": [
        "入口くぐり", "入口ループ", "大ループ", "エンドループ", "エンドちぢれ",
        "先端飛びだし", "途中切れ", "捨耳掴まず", "上糸くぐり", "下糸くぐり",
        "ムダ止まり", "ロングピック（長尺）", "ショートピック（短尺）", "ドラム～メイン間切れ", "カッターミス"
    ]
}

change_areas = [
    "バック", "ドロッパ", "イージング", "テンプル", "耳", "緯入れ-メイン系",
    "カッター", "開口角", "開口量", "枠高さ", "ドエル", "クロスタイミング",
    "エア圧力", "タオル", "緯入れ-サブ系", "張力", "Motor設定", "MARK設定",
    "T0-Tw", "Tw-Ctrl", "フィーラ設定", "その他"
]

# ********************************************************************************
# ファイルアップロード処理
# ********************************************************************************
@app.route("/", methods=["GET", "POST"])
def upload_file():
    try:
        if request.method == "POST":
            uploaded_file = request.files["file"]
            if uploaded_file.filename:
                file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
                uploaded_file.save(file_path)  # ファイルを保存
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
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 基本情報入力処理
# ********************************************************************************
@app.route("/save", methods=["POST"])
def save_data():
    try:
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("ファイル名がセッションに存在しません")

        # 基本情報をセッションに保存
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
        session["phenomena"] = []  # 現象データも初期化

        # 現象データ入力画面を表示
        return render_template(
            "phenomenon.html",
            file_name=file_name,
            categories=category_mapping,
            change_areas=change_areas,
            phenomena=session.get("phenomena", [])
        )
    except Exception as e:
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 現象データ入力処理
# ********************************************************************************
@app.route("/phenomenon", methods=["POST"])
def phenomenon_input():
    try:
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("ファイル名がセッションに存在しません")

        # フォームデータを取得して現象データを保存
        category = request.form["category"]
        subcategory = request.form["subcategory"]
        change_area = request.form["change_area"]

        # 現象データをセッションに追加
        phenomena = session.get("phenomena", [])
        phenomena.append((category, subcategory, change_area))
        session["phenomena"] = phenomena

        return render_template(
            "phenomenon.html",
            file_name=file_name,
            categories=category_mapping,
            change_areas=change_areas,
            phenomena=session["phenomena"]
        )
    except Exception as e:
        print("エラー:", str(e))
        return "サーバーエラー: " + str(e), 500

# ********************************************************************************
# 現象データ保存処理
# ********************************************************************************
@app.route("/save_phenomena", methods=["POST"])
def save_phenomena():
    try:
        file_name = session.get("current_file")
        if not file_name:
            raise Exception("ファイル名がセッションに存在しません")

        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        if not os.path.exists(file_path):
            raise Exception(f"元のファイルが存在しません: {file_path}")

        # 現象データを取得
        phenomena = session.get("phenomena", [])
        processed_file_path = os.path.join(UPLOAD_FOLDER, f"processed_{file_name}")

        # 現象データを処理してファイルに保存
        phenomenon_lines = ['"JAT910-Phenomenon DATA -----------"\n']
        for category, subcategory, change_area in phenomena:
            phenomenon_lines.append(f'"{category}","{subcategory}","{change_area}"\n')

        with open(processed_file_path, "w", encoding="utf-8") as processed_file:
            with open(file_path, "r", encoding="utf-8") as original_file:
                processed_file.writelines(original_file.readlines())
            processed_file.writelines(phenomenon_lines)

        return send_file(processed_file_path, as_attachment=True)
    except Exception as e:
        print("エラー:", str(e))
        return f"サーバーエラー: {str(e)}", 500

# ********************************************************************************
# サーバー起動処理
# ********************************************************************************
if __name__ == "__main__":
    app.run(debug=True)